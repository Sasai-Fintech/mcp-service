#!/usr/bin/env python3
"""
Kubernetes-ready HTTP entry point for Sasai Wallet Operations MCP Server.

This entry point provides production-ready HTTP-based access to the MCP server 
with proper health endpoints for Kubernetes readiness/liveness probes.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Ensure we can import from our src directory
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import from our modular structure
from core.server import initialize_server
from config.settings import SasaiConfig
from utils.helpers import setup_logging


# Global variables for health checks
mcp_server = None
mcp_server_ready = False
mcp_server_error = None


def create_fastapi_app():
    """Create FastAPI app with health endpoints for Kubernetes."""
    app = FastAPI(
        title="Sasai Wallet MCP Server",
        description="MCP Server with Kubernetes health endpoints",
        version="2.0.0"
    )
    
    @app.get("/health")
    async def health_check():
        """Standard Kubernetes readiness probe endpoint."""
        global mcp_server_error
        
        # Always return 200 for basic health (server is running)
        if mcp_server_error:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "mcp_server": "error",
                    "error": str(mcp_server_error),
                    "service": "sasai-wallet-mcp",
                    "version": "2.0.0"
                }
            )
        
        return JSONResponse({
            "status": "healthy" if mcp_server_ready else "starting",
            "mcp_server": "ready" if mcp_server_ready else "starting",
            "service": "sasai-wallet-mcp",
            "version": "2.0.0"
        })
    
    @app.get("/health/readiness")
    async def readiness_probe():
        """Kubernetes readiness probe endpoint (matches your K8s config)."""
        global mcp_server_error
        
        # Check if MCP server failed
        if mcp_server_error:
            raise HTTPException(
                status_code=503, 
                detail={
                    "ready": False,
                    "error": str(mcp_server_error),
                    "service": "sasai-wallet-mcp"
                }
            )
        
        # For readiness, we can be more lenient with config validation
        # since missing env vars should not prevent the pod from being ready
        if not mcp_server_ready:
            raise HTTPException(
                status_code=503,
                detail={
                    "ready": False,
                    "mcp_server": "not_ready",
                    "service": "sasai-wallet-mcp"
                }
            )
        
        return JSONResponse({
            "ready": True,
            "mcp_server": "ready",
            "service": "sasai-wallet-mcp",
            "version": "2.0.0",
            "environment": getattr(SasaiConfig, "ENVIRONMENT", "unknown")
        })
    
    @app.get("/health/liveness")
    async def liveness_probe():
        """Kubernetes liveness probe endpoint."""
        return JSONResponse({
            "status": "alive",
            "service": "sasai-wallet-mcp",
            "version": "2.0.0"
        })
    
    @app.get("/healthz")
    async def liveness_check():
        """Alternative Kubernetes liveness probe endpoint."""
        return JSONResponse({
            "status": "alive",
            "service": "sasai-wallet-mcp",
            "version": "2.0.0"
        })
    
    @app.get("/ready")
    async def detailed_readiness():
        """Detailed readiness check with configuration validation."""
        global mcp_server_error
        
        try:
            # Test configuration but don't fail if env vars are missing
            config_issues = []
            try:
                config_valid = SasaiConfig.validate_configuration()
                config_issues = config_valid.get("issues", [])
                config_valid_flag = config_valid.get("valid", False)
            except Exception as e:
                config_issues = [f"Config validation error: {str(e)}"]
                config_valid_flag = False
            
            ready_status = {
                "ready": mcp_server_ready and not mcp_server_error,
                "mcp_server": "ready" if mcp_server_ready else ("error" if mcp_server_error else "starting"),
                "configuration": "valid" if config_valid_flag else "invalid",
                "config_issues": config_issues,
                "environment": getattr(SasaiConfig, "ENVIRONMENT", "unknown"),
                "base_url": getattr(SasaiConfig, "BASE_URL", "unknown"),
                "service": "sasai-wallet-mcp",
                "version": "2.0.0"
            }
            
            if mcp_server_error:
                ready_status["error"] = str(mcp_server_error)
            
            # For detailed endpoint, show issues but don't necessarily fail
            return JSONResponse(ready_status)
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "ready": False, 
                    "error": str(e), 
                    "service": "sasai-wallet-mcp"
                }
            )
    
    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        return JSONResponse({
            "service": "sasai-wallet-mcp",
            "version": "2.0.0",
            "mcp_endpoint": "/mcp",
            "health_endpoints": {
                "health": "/health",
                "readiness": "/health/readiness",
                "liveness": "/health/liveness", 
                "detailed": "/ready"
            },
            "environment": getattr(SasaiConfig, "ENVIRONMENT", "unknown"),
            "status": "running",
            "mcp_server_status": "ready" if mcp_server_ready else "starting"
        })
    
    return app


async def run_mcp_server():
    """Run the MCP server in a separate task."""
    global mcp_server, mcp_server_ready, mcp_server_error
    
    try:
        print("🔧 Initializing MCP server...")
        
        # Initialize the server with all tools
        mcp_server = initialize_server()
        print("✅ MCP server initialized successfully")
        
        # Configure MCP HTTP settings
        host = "127.0.0.1"  # Internal only for MCP
        port = int(os.getenv("MCP_INTERNAL_PORT", "8001"))  # Different port for internal MCP
        path = "/mcp"
        
        logger = setup_logging(level=getattr(SasaiConfig, "LOG_LEVEL", "INFO"))
        logger.info(f"Starting internal MCP server on {host}:{port}{path}")
        
        # Mark server as ready BEFORE starting to avoid blocking
        mcp_server_ready = True
        print(f"✅ MCP server ready on {host}:{port}{path}")
        
        # Use the production-ready streamable HTTP transport
        await mcp_server.run_streamable_http_async(
            host=host,
            port=port,
            path=path,
            log_level=getattr(SasaiConfig, "LOG_LEVEL", "INFO")
        )
            
    except Exception as e:
        mcp_server_ready = False
        mcp_server_error = e
        print(f"❌ MCP server failed: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't re-raise - let health checks report the error


async def main():
    """Entry point for Kubernetes-ready HTTP server."""
    try:
        print("🚀 Starting Kubernetes-ready Sasai Wallet MCP Server")
        
        # Set up basic logging first
        try:
            logger = setup_logging(level=getattr(SasaiConfig, "LOG_LEVEL", "INFO"))
        except Exception as e:
            print(f"⚠️ Logging setup failed: {e}, using basic logging")
            import logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)
        
        # Configure main HTTP settings for Kubernetes
        host = os.getenv("HTTP_HOST", "0.0.0.0")  # Listen on all interfaces
        port = int(os.getenv("PORT", "8000"))  # Railway/Kubernetes standard
        
        print(f"📡 Health endpoints: http://{host}:{port}/health")
        print(f"🔧 Host: {host}")
        print(f"🔧 Port: {port}")
        print(f"🔧 Transport: HTTP + MCP Streamable")
        print("---")
        print("🩺 Kubernetes Health Endpoints:")
        print(f"   Readiness: http://{host}:{port}/health/readiness")
        print(f"   Liveness:  http://{host}:{port}/health/liveness")
        print(f"   Detailed:  http://{host}:{port}/ready")
        print("---")
        print("📖 MCP Client Connection:")
        print(f"   Internal MCP: http://127.0.0.1:8001/mcp")
        print("   (External clients should use load balancer/ingress)")
        print("---")
        
        logger.info(f"Starting Kubernetes-ready server on {host}:{port}")
        
        # Create FastAPI app with health endpoints
        app = create_fastapi_app()
        
        # Start MCP server in background task (don't await)
        asyncio.create_task(run_mcp_server())
        
        # Start FastAPI server with health endpoints
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",  # Use fixed log level for uvicorn
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
            
    except KeyboardInterrupt:
        print("\n\n👋 Server shutdown requested by user")
        print("Goodbye!")
    except Exception as e:
        print(f"\n❌ Kubernetes server startup failed: {str(e)}")
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
