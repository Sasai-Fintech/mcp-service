#!/usr/bin/env python3
"""
Main entry point for the FastMCP Sasai Wallet Operations Server.

This module serves as the entry point for the production-grade FastMCP server
that provides comprehensive wallet operations for the Sasai Payment Gateway.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path for imports
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Import modules from our package structure
from core.server import initialize_server
from config.settings import SasaiConfig
from utils.helpers import setup_logging, load_environment_variables




def main():
    """Main function to run the FastMCP server."""
    try:
        # Set up logging
        logger = setup_logging(level=SasaiConfig.LOG_LEVEL)
        server = initialize_server()
        
        print("🎯 Server Initialization Complete!")
        
        # Run the server (uses STDIO transport by default)
        logger.info("Starting MCP server with STDIO transport")
        server.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested by user")
        print("Goodbye!")
    except Exception as e:
        print(f"\n❌ Server startup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
