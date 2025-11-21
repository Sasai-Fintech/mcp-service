#!/usr/bin/env python3
"""
Claude Desktop entry point for Sasai Wallet Operations MCP Server.

This is the main entry point specifically configured for Claude Desktop integration.
It uses the modular structure from src/ but provides a clean interface for Claude.
"""

import sys
import os
from pathlib import Path

# Ensure we can import from our src directory
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import from our modular structure
from core.server import initialize_server
from config.settings import SasaiConfig
from utils.helpers import setup_logging

def main():
    """Entry point for Claude Desktop integration."""
    try:
        # Set up minimal logging for Claude Desktop
        logger = setup_logging(level="WARNING")  # Less verbose for Claude Desktop
        
        # Initialize the server with all tools
        server = initialize_server()
        
        # Run with STDIO transport (required for Claude Desktop)
        server.run()
        
    except KeyboardInterrupt:
        # Clean shutdown
        pass
    except Exception as e:
        # Log error but don't crash Claude Desktop
        import logging
        logging.error(f"FastMCP server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
