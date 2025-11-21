"""Health monitoring operations for FastMCP server."""

import asyncio
import httpx
from typing import Dict, Any

from config import SasaiConfig
from auth.manager import token_manager
from auth.tools import generate_authentication_token


def register_monitoring_tools(mcp_server) -> None:
    """
    Register wallet health monitoring tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def wallet_health_check() -> Dict[str, Any]:
        """
        Check the health status of the Sasai Wallet Payment Gateway API.
        
        This tool performs comprehensive health checks on wallet-related endpoints
        to ensure the wallet services are operational and accessible.
        
        Returns:
            dict: Wallet health status information including API availability and authentication status
        """
        # Test multiple endpoints to get comprehensive health status
        endpoints_to_test = [
            ("wallet_balance", SasaiConfig.ENDPOINTS.wallet_balance),
            ("transaction_history", SasaiConfig.ENDPOINTS.transaction_history),
            ("linked_cards", SasaiConfig.ENDPOINTS.linked_cards),
            ("customer_profile", SasaiConfig.ENDPOINTS.customer_profile)
        ]
        
        # Use current token if available, otherwise try to generate one
        token_to_use = token_manager.get_token()
        if not token_to_use:
            try:
                token_result = await generate_authentication_token()
                if token_result.get("success"):
                    token_to_use = token_manager.get_token()
            except:
                pass  # Continue with health check even if token generation fails
        
        health_results = {
            "overall_status": "healthy",
            "api_reachable": True,
            "authentication_working": True,
            "token_available": token_to_use is not None,
            "endpoint_tests": {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        failed_endpoints = 0
        
        for endpoint_name, endpoint_url in endpoints_to_test:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                    headers = SasaiConfig.DEFAULT_HEADERS.copy()
                    if token_to_use:
                        headers["Authorization"] = f"Bearer {token_to_use}"
                    
                    # Test with minimal parameters
                    test_params = {}
                    test_json_data = None
                    
                    if endpoint_name == "wallet_balance":
                        test_params = {"currency": "USD", "providerCode": "ecocash"}
                        response = await client.get(endpoint_url, params=test_params, headers=headers)
                    elif endpoint_name == "transaction_history":
                        # Transaction history requires POST with JSON payload including PIN
                        test_json_data = {
                            "pin": SasaiConfig.get_auth_credentials().pin,
                            "currency": "USD",
                            "page": 0,
                            "pageSize": 1
                        }
                        response = await client.post(endpoint_url, json=test_json_data, headers=headers)
                    elif endpoint_name == "linked_cards":
                        # Linked cards is a simple GET request without parameters
                        response = await client.get(endpoint_url, headers=headers)
                    else:
                        # For other endpoints, use GET without parameters
                        response = await client.get(endpoint_url, headers=headers)
                    
                    health_results["endpoint_tests"][endpoint_name] = {
                        "status": "healthy" if response.status_code < 500 else "unhealthy",
                        "status_code": response.status_code,
                        "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                        "authenticated": response.status_code != 401
                    }
                    
                    if response.status_code >= 500:
                        failed_endpoints += 1
                    elif response.status_code == 401:
                        health_results["authentication_working"] = False
                        
            except Exception as e:
                health_results["endpoint_tests"][endpoint_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "authenticated": False
                }
                failed_endpoints += 1
        
        # Update overall status based on results
        if failed_endpoints == len(endpoints_to_test):
            health_results["overall_status"] = "unhealthy"
            health_results["api_reachable"] = False
        elif failed_endpoints > 0:
            health_results["overall_status"] = "degraded"
        
        return health_results
