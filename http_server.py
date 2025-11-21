#!/usr/bin/env python3
"""
HTTP entry point for Sasai Wallet Operations MCP Server.

This entry point provides HTTP-based access to the MCP server using Server-Sent Events (SSE).
It allows web-based clients and tools to interact with the wallet operations via HTTP.
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
    """Entry point for HTTP-based MCP server."""
    try:
        # Set up logging
        logger = setup_logging(level=SasaiConfig.LOG_LEVEL)
        
        # Initialize the server with all tools
        server = initialize_server()
        
        # Configure HTTP settings
        host = os.getenv("MCP_HTTP_HOST", "localhost")
        port = int(os.getenv("MCP_HTTP_PORT", "8000"))
        path = os.getenv("MCP_HTTP_PATH", "/sse")
        transport_type = os.getenv("MCP_TRANSPORT", "sse")  # Options: 'sse', 'http', 'streamable-http'
        
        print(f"🚀 Starting Sasai Wallet MCP Server (HTTP - {transport_type.upper()})")
        print(f"📡 Server URL: http://{host}:{port}{path}")
        print(f"🔧 Host: {host}")
        print(f"🔧 Port: {port}")
        print(f"🔧 Path: {path}")
        print(f"🔧 Transport: {transport_type}")
        print("---")
        print("💡 Usage:")
        print(f"   Connect MCP clients to: http://{host}:{port}{path}")
        print(f"   Health check available at server endpoint")
        print("---")
        
        logger.info(f"Starting MCP server with {transport_type} transport on {host}:{port}")
        
        # Choose transport method based on configuration
        if transport_type == "sse":
            await server.run_sse_async(
                host=host,
                port=port,
                path=path,
                log_level=SasaiConfig.LOG_LEVEL
            )
        elif transport_type == "http":
            await server.run_http_async(
                transport="http",
                host=host,
                port=port,
                path=path,
                log_level=SasaiConfig.LOG_LEVEL,
                show_banner=True
            )
        elif transport_type == "streamable-http":
            await server.run_streamable_http_async(
                host=host,
                port=port,
                path=path,
                log_level=SasaiConfig.LOG_LEVEL
            )
        else:
            raise ValueError(f"Unknown transport type: {transport_type}")
            
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested by user")
        print("Goodbye!")
    except Exception as e:
        print(f"\n❌ HTTP server startup failed: {str(e)}")
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
