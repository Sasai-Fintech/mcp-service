#!/usr/bin/env python3
"""
Streamable HTTP entry point for Sasai Wallet Operations MCP Server.

This entry point provides production-ready HTTP-based access to the MCP server 
using the recommended Streamable HTTP transport for efficient bidirectional streaming.
"""

import sys
import os
import asyncio
from pathlib import Path

# Ensure we can import from our src directory
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import from our modular structure
from core.server import initialize_server
from config.settings import SasaiConfig
from utils.helpers import setup_logging


async def main():
    """Entry point for Streamable HTTP-based MCP server."""
    try:
        # Set up logging
        logger = setup_logging(level=SasaiConfig.LOG_LEVEL)
        
        # Initialize the server with all tools
        server = initialize_server()
        
        # Configure HTTP settings
        host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")  # Changed to 0.0.0.0 for production
        port = int(os.getenv("MCP_HTTP_PORT", "8000"))
        path = os.getenv("MCP_HTTP_PATH", "/mcp")  # Standard path for MCP
        
        print(f"🚀 Starting Sasai Wallet MCP Server (Streamable HTTP)")
        print(f"📡 Server URL: http://{host}:{port}{path}")
        print(f"🔧 Host: {host}")
        print(f"🔧 Port: {port}")
        print(f"🔧 Path: {path}")
        print(f"🔧 Transport: Streamable HTTP (Production)")
        print("---")
        print("💡 Client Connection:")
        print(f"   URL: http://{host}:{port}{path}")
        print("   Transport: StreamableHttpTransport")
        print("---")
        print("📖 Example Client Code:")
        print("   from fastmcp.client.transports import StreamableHttpTransport")
        print(f"   transport = StreamableHttpTransport(url='http://{host}:{port}{path}')")
        print("   client = Client(transport)")
        print("---")
        
        logger.info(f"Starting MCP server with Streamable HTTP transport on {host}:{port}")
        
        # Use the production-ready streamable HTTP transport
        # Switching to SSE transport for compatibility with standard MCP client
        await server.run_http_async(
            transport="sse",
            host=host,
            port=port,
            path=path,
            log_level=SasaiConfig.LOG_LEVEL
        )
            
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested by user")
        print("Goodbye!")
    except Exception as e:
        print(f"\n❌ Streamable HTTP server startup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main_sync():
    """Synchronous wrapper for the async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested by user")
        print("Goodbye!")


if __name__ == "__main__":
    main_sync()
