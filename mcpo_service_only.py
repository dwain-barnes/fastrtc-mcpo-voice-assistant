from ollama_mcpo_adapter import MCPOService
import time
import signal
import sys

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\nReceived interrupt signal. Stopping MCPO service...')
    if 'mcpo' in globals():
        mcpo.stop()
    print("MCPO service stopped")
    sys.exit(0)

def main():
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Define MCP configuration
    mcp_config = {
        "mcpServers": {
            "time": {
                "command": "uvx", 
                "args": ["mcp-server-time", "--local-timezone=Europe/London"]
            },
            "airbnb": {
                "command": "npx",
                "args": [
                    "-y",
                    "@openbnb/mcp-server-airbnb",
                    "--ignore-robots-txt"
                ]
            }
        }
    }

    # Initialize MCPO service
    print("Starting MCPO service...")
    global mcpo
    mcpo = MCPOService("127.0.0.1", 8000, config=mcp_config)
    
    try:
        # Start MCPO service
        mcpo.start(wait=True)
        print("✓ MCPO service started successfully on port 8000")
        print("✓ Time server configured for Europe/London timezone")
        print("✓ Airbnb server configured with robots.txt ignored")
        print("✓ Available endpoints:")
        print("  Time Tools:")
        print("    - http://127.0.0.1:8000/time/get_current_time")
        print("    - http://127.0.0.1:8000/time/convert_time")
        print("  Airbnb Tools:")
        print("    - http://127.0.0.1:8000/airbnb/* (various search endpoints)")
        print("  Documentation:")
        print("    - http://127.0.0.1:8000/docs (API documentation)")
        print("\nMCPO service is running with multiple MCP servers. Press Ctrl+C to stop.")
        
        # Keep the service running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always stop MCPO service
        print("Stopping MCPO service...")
        mcpo.stop()
        print("MCPO service stopped")

if __name__ == "__main__":
    print("=== MCPO Multi-Server Service Runner ===")
    print("This starts and runs the MCPO service with multiple MCP servers:")
    print("  - Time tools (get current time, convert time zones)")
    print("  - Airbnb tools (search listings, get property details)")
    print("Run this in one terminal, then use the client in another")
    print()
    
    main()