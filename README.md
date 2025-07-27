# MCPO Voice Assistant

A voice-enabled AI assistant that converts **MCP (Model Context Protocol) servers** into **OpenAI API tool format** and provides real-time voice interaction through FastRTC and Ollama.

## 🚀 What This Does

This project bridges MCP servers and OpenAI-compatible LLMs by:

1. **Converting MCP servers to OpenAI tools** - Takes MCP servers and exposes them as OpenAI function calling format
2. **Voice interface** - Real-time speech-to-text and text-to-speech using FastRTC
3. **Tool integration** - Seamlessly call MCP tools through voice commands
4. **Multi-server support** - Run multiple MCP servers simultaneously

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Voice Input   │───▶│   FastRTC STT    │───▶│     Ollama      │
│   (Microphone)  │    │                  │    │   (LLM Model)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Voice Output   │◀───│   FastRTC TTS    │◀───│ MCPO Adapter    │
│   (Speakers)    │    │                  │    │ (MCP→OpenAI)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                          ┌─────────────────────────────┐
                                          │       MCP Servers           │
                                          │  ┌─────────────────────┐    │
                                          │  │   Time Server       │    │
                                          │  │   (Timezone ops)    │    │
                                          │  └─────────────────────┘    │
                                          │  ┌─────────────────────┐    │
                                          │  │   Airbnb Server     │    │
                                          │  │   (Property search) │    │
                                          │  └─────────────────────┘    │
                                          └─────────────────────────────┘
```

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- Node.js (for MCP servers)
- Ollama installed and running
- FastRTC dependencies

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dwain-barnes/fastrtc-mcpo-voice-assistant.git
   cd fastrtc-mcpo-voice-assistant
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install manually:
   ```bash
   pip install "fastrtc[vad,stt,tts]"
   pip install ollama-mcpo-adapter
   pip install ollama requests
   ```

3. **Install MCP servers**
   ```bash
   # Time server
   uvx mcp-server-time
   
   # Airbnb server
   npx -y @openbnb/mcp-server-airbnb
   ```

4. **Start Ollama**
   ```bash
   ollama serve
   ollama pull mistral-small3.2:latest
   ```

## 🚀 Usage

### Step 1: Start the MCPO Service

The MCPO service converts MCP servers to OpenAI API format:

```bash
python mcpo_service_only.py
```

This starts a service on `http://127.0.0.1:8000` with endpoints:
- **Time Tools**: `/time/get_current_time`, `/time/convert_time`
- **Airbnb Tools**: `/airbnb/*` (various search endpoints)
- **Documentation**: `/docs` (API documentation)

### Step 2: Start the Voice Assistant

In a new terminal:

```bash
python fastrtc_mcpo_voice.py
```

This opens a web interface at `http://127.0.0.1:7860` where you can:
- Click "Start" to begin voice interaction
- Speak naturally to the assistant
- Get voice responses with tool integration

## 🎯 Example Voice Commands

### Time Queries
- *"What time is it in London?"*
- *"Convert 3 PM London time to New York time"*
- *"What's the current time in Tokyo?"*

### Airbnb Searches
- *"Find Airbnb in Paris for one person"*
- *"Search for apartments in Barcelona"*
- *"Show me accommodations in Rome"*

### Combined Requests
- *"What time is it in Tokyo and find hotels there"*

## 📁 Project Structure

```
├── mcpo_service_only.py      # MCPO service runner
├── fastrtc_mcpo_voice.py     # Voice assistant with tool integration
├── ollama_mcpo_adapter.py    # MCP to OpenAI adapter (your module)
└── README.md                 # This file
```

## 🔧 Configuration

### MCP Server Configuration

Edit the `mcp_config` in `mcpo_service_only.py`:

```python
mcp_config = {
    "mcpServers": {
        "time": {
            "command": "uvx", 
            "args": ["mcp-server-time", "--local-timezone=Europe/London"]
        },
        "airbnb": {
            "command": "npx",
            "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]
        },
        # Add more MCP servers here
    }
}
```

### Voice Models

The voice assistant uses:
- **STT**: `moonshine/base` (Speech-to-Text)
- **TTS**: `kokoro` (Text-to-Speech)
- **LLM**: `mistral-small3.2:latest` (via Ollama)

## 🎛️ Features

### Voice Processing
- **Real-time STT/TTS** using FastRTC
- **Natural conversation flow** with pause detection
- **Clean text processing** removes formatting for better voice output

### Tool Integration
- **Automatic tool discovery** from MCPO service
- **Smart result formatting** for voice-friendly responses
- **Error handling** with graceful fallbacks

### MCP Server Support
- **Multiple server support** - Run any number of MCP servers
- **Dynamic tool loading** - Tools automatically available to LLM
- **OpenAI compatibility** - Standard function calling format

## 🔍 How MCP-to-OpenAI Conversion Works

1. **MCP servers** expose tools in MCP format
2. **MCPO adapter** discovers available tools from MCP servers
3. **Tool conversion** transforms MCP tool schemas to OpenAI function format
4. **Ollama integration** receives tools in standard OpenAI function calling format
5. **Execution bridge** routes function calls back to appropriate MCP servers

## 🛡️ Error Handling

- **Graceful degradation** - Works without MCPO service
- **Connection monitoring** - Checks service availability
- **Voice feedback** - Announces errors through speech
- **Clean shutdown** - Proper signal handling with Ctrl+C

## 🎨 Customization

### Add New MCP Servers

1. Install the MCP server
2. Add to `mcp_config` in `mcpo_service_only.py`
3. Restart the MCPO service

### Modify Voice Behavior

Edit the `SYSTEM_PROMPT` in `fastrtc_mcpo_voice.py`:

```python
SYSTEM_PROMPT = """You are a helpful voice assistant...
# Customize behavior here
"""
```

## 🙏 Acknowledgments

- **https://github.com/tappi287/ollama-mcpo-adapter**
- **FastRTC** for real-time voice processing
- **Ollama** for local LLM serving
- **OpenAI** for function calling standards

---

**Ready to talk to your tools? Start the services and say hello!** 🎤
