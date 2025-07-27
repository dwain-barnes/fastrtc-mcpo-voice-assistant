from fastrtc import ReplyOnPause, Stream, get_stt_model, get_tts_model
from ollama import Client
from ollama_mcpo_adapter import OllamaMCPOAdapter
import requests
import re
import json

# Initialize TTS/STT models
stt_model = get_stt_model(model="moonshine/base")
tts_model = get_tts_model(model="kokoro")

# Initialize Ollama client
ollama_client = Client(host="http://127.0.0.1:11434")

SYSTEM_PROMPT = """You are a helpful voice assistant with access to time and Airbnb tools. 
Keep responses conversational, brief, and natural for voice conversations. 

For Airbnb searches:
- Mention only the top 2-3 best options with key details (name, price, rating)
- Don't mention URLs, listing IDs, or coordinates 
- Focus on practical info like price per night and guest ratings
- Avoid repetitive information

For time queries:
- Give simple, clear time information
- Mention timezone and whether it's daylight saving time if relevant

Never use asterisks, bullet points, markdown, or any formatting in responses.
Keep everything conversational and easy to understand when spoken aloud."""

# Global variables for tools
tools = []
adapter = None

def clean_text_for_tts(text):
    """Clean text for TTS by removing formatting and emojis"""
    if not text:
        return ""
    
    # Remove asterisks and markdown formatting
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'`+', '', text)
    
    # Remove bullet points and list markers
    text = re.sub(r'^\s*[-•*]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Remove emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def format_airbnb_results_for_voice(tool_results):
    """Format Airbnb results to be more voice-friendly"""
    try:
        for result in tool_results:
            if isinstance(result, dict) and 'searchResults' in result:
                search_results = result['searchResults']
                
                # Remove duplicates based on ID
                unique_results = {}
                for listing in search_results:
                    listing_id = listing.get('id')
                    if listing_id and listing_id not in unique_results:
                        unique_results[listing_id] = listing
                
                # Sort by price and rating, get top 3
                sorted_results = sorted(
                    unique_results.values(),
                    key=lambda x: (
                        # Prefer higher ratings
                        -float(re.findall(r'(\d+\.?\d*)', x.get('avgRatingA11yLabel', '0'))[0] if re.findall(r'(\d+\.?\d*)', x.get('avgRatingA11yLabel', '0')) else 0),
                        # Then prefer lower prices
                        float(re.findall(r'£(\d+)', x.get('structuredDisplayPrice', {}).get('primaryLine', {}).get('accessibilityLabel', '£999'))[0] if re.findall(r'£(\d+)', x.get('structuredDisplayPrice', {}).get('primaryLine', {}).get('accessibilityLabel', '£999')) else 999)
                    )
                )[:3]
                
                # Create voice-friendly summary
                if sorted_results:
                    summary = f"I found {len(unique_results)} Airbnb listings. Here are the top options:\n\n"
                    
                    for i, listing in enumerate(sorted_results, 1):
                        name = listing.get('demandStayListing', {}).get('description', {}).get('name', {}).get('localizedStringWithTranslationPreference', f'Listing {i}')
                        
                        price_info = listing.get('structuredDisplayPrice', {}).get('primaryLine', {}).get('accessibilityLabel', 'Price not available')
                        price_match = re.search(r'£(\d+)', price_info)
                        price = f"£{price_match.group(1)}" if price_match else "Price varies"
                        
                        rating_info = listing.get('avgRatingA11yLabel', '')
                        rating_match = re.search(r'(\d+\.?\d*) out of 5', rating_info)
                        rating = f"{rating_match.group(1)} out of 5" if rating_match else "No rating"
                        
                        summary += f"{i}. {name}\n"
                        summary += f"   Price: {price} per night\n"
                        summary += f"   Rating: {rating}\n\n"
                    
                    # Replace the verbose result with clean summary
                    result['voice_summary'] = summary
                    
        return tool_results
        
    except Exception as e:
        print(f"Error formatting Airbnb results: {e}")
        return tool_results

def format_time_results_for_voice(tool_results):
    """Format time results to be more voice-friendly"""
    try:
        for result in tool_results:
            if isinstance(result, dict) and 'datetime' in result:
                # Extract readable time from datetime
                datetime_str = result.get('datetime', '')
                timezone = result.get('timezone', '')
                
                if datetime_str:
                    # Parse time (e.g., "2025-07-27T11:57:05+01:00")
                    time_match = re.search(r'T(\d{2}):(\d{2})', datetime_str)
                    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', datetime_str)
                    
                    if time_match and date_match:
                        hour, minute = time_match.groups()
                        year, month, day = date_match.groups()
                        
                        # Convert to 12-hour format
                        hour_int = int(hour)
                        am_pm = "AM" if hour_int < 12 else "PM"
                        if hour_int == 0:
                            hour_12 = 12
                        elif hour_int > 12:
                            hour_12 = hour_int - 12
                        else:
                            hour_12 = hour_int
                        
                        time_str = f"{hour_12}:{minute} {am_pm}"
                        
                        # Get timezone info
                        is_dst = result.get('is_dst', False)
                        dst_info = " (daylight saving time)" if is_dst else ""
                        
                        voice_summary = f"The current time in {timezone.replace('_', ' ').replace('/', ', ')} is {time_str}{dst_info}."
                        result['voice_summary'] = voice_summary
                        
        return tool_results
        
    except Exception as e:
        print(f"Error formatting time results: {e}")
        return tool_results

def initialize_mcpo_tools():
    """Initialize MCPO adapter and get tools"""
    global tools, adapter
    
    try:
        # Check if MCPO is running
        response = requests.get("http://127.0.0.1:8000/openapi.json", timeout=5)
        if response.status_code != 200:
            print("Warning: MCPO service not running. Voice assistant will work without tools.")
            return False
            
        # Initialize adapter and get tools
        adapter = OllamaMCPOAdapter("127.0.0.1", 8000)
        tools = adapter.list_tools_ollama()
        
        print(f"✓ Voice assistant initialized with {len(tools)} tools:")
        for tool in tools:
            tool_name = tool.get('function', {}).get('name', 'unknown')
            print(f"  - {tool_name}")
        return True
        
    except Exception as e:
        print(f"Warning: Could not connect to MCPO tools: {e}")
        print("Voice assistant will work without tools.")
        return False

def echo(audio):
    """Process voice input and return voice response with tool support"""
    try:
        # Convert speech to text
        transcript = stt_model.stt(audio)
        print(f"User said: {transcript}")
        
        if not transcript.strip():
            return
        
        # Get initial response from Ollama with tools
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript}
        ]
        
        if tools:
            response = ollama_client.chat(
                model="mistral-small3.2:latest", 
                messages=messages,
                tools=tools
            )
        else:
            response = ollama_client.chat(
                model="mistral-small3.2:latest", 
                messages=messages
            )
        
        response_text = response.message.content
        
        # Handle tool calls if present
        if tools and response.message.tool_calls:
            print(f"Executing {len(response.message.tool_calls)} tool calls...")
            
            try:
                # Execute tools using adapter
                tool_results = adapter.call_tools_from_response(response.message.tool_calls)
                
                # Format results for voice
                tool_results = format_time_results_for_voice(tool_results)
                tool_results = format_airbnb_results_for_voice(tool_results)
                
                # Create voice-friendly tool content
                voice_tool_content = []
                for result in tool_results:
                    if isinstance(result, dict):
                        if 'voice_summary' in result:
                            voice_tool_content.append(result['voice_summary'])
                        elif 'datetime' in result:
                            # Time result without voice_summary
                            voice_tool_content.append(str(result))
                        elif 'searchResults' in result:
                            # Airbnb result without voice_summary
                            voice_tool_content.append(f"Found {len(result.get('searchResults', []))} Airbnb listings.")
                        else:
                            voice_tool_content.append(str(result))
                    else:
                        voice_tool_content.append(str(result))
                
                # Add tool results to conversation
                messages.append({
                    "role": "assistant", 
                    "content": response_text, 
                    "tool_calls": response.message.tool_calls
                })
                
                # Add formatted tool results
                for i, tool_call in enumerate(response.message.tool_calls):
                    content = voice_tool_content[i] if i < len(voice_tool_content) else "No result"
                    messages.append({
                        "role": "tool",
                        "content": content,
                        "tool_call_id": getattr(tool_call, 'id', f'call_{i}')
                    })
                
                # Get final response with tool data
                final_response = ollama_client.chat(
                    model="mistral-small3.2:latest",
                    messages=messages,
                    tools=tools
                )
                
                response_text = final_response.message.content
                print(f"Final response: {response_text}")
                
            except Exception as e:
                print(f"Error executing tools: {e}")
                response_text = f"I had trouble accessing the tools, but I can tell you: {response_text}"
        
        # Clean text for TTS and convert to speech
        if response_text:
            # Clean the text before TTS
            clean_response = clean_text_for_tts(response_text)
            print(f"Assistant: {clean_response}")
            
            for audio_chunk in tts_model.stream_tts_sync(clean_response):
                yield audio_chunk
        
    except Exception as e:
        print(f"Error in echo function: {e}")
        error_message = "Sorry, I had trouble processing that request."
        for audio_chunk in tts_model.stream_tts_sync(error_message):
            yield audio_chunk

def main():
    """Main function to start the voice assistant"""
    print("=== FastRTC Voice Assistant with MCPO Tools ===")
    print("Initializing...")
    
    # Initialize MCPO tools
    tools_available = initialize_mcpo_tools()
    
    if tools_available:
        print("\n✓ Voice assistant ready with time and Airbnb tools!")
        print("Try saying:")
        print("  - 'What time is it in London?'")
        print("  - 'Find Airbnb in Paris for one person'")
        print("  - 'Convert 3 PM London time to New York time'")
        print("  - 'Search for apartments in Barcelona'")
        print("  - 'What time is it in Tokyo and find hotels there'")
    else:
        print("\n✓ Voice assistant ready (without MCPO tools)")
        print("To enable tools, make sure MCPO service is running:")
        print("  python mcpo_service.py")
    
    print("\nStarting voice interface...")
    print("The web interface will open at http://127.0.0.1:7860")
    print("Click 'Start' and begin speaking!")
    
    # Create and launch stream
    stream = Stream(ReplyOnPause(echo), modality="audio", mode="send-receive")
    stream.ui.launch()

if __name__ == "__main__":
    main()