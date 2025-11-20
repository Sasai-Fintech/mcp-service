"""Airtime plans operations for FastMCP server."""

from typing import Literal, Optional, Dict, Any

from config import SasaiConfig
from api import SasaiAPIClient
from auth.manager import token_manager
from auth.tools import generate_authentication_token


def register_airtime_tools(mcp_server) -> None:
    """
    Register wallet airtime plans tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_wallet_airtime_plans(
        provider: Optional[Literal["econet", "netone", "telecel"]] = None,
        plan_type: Optional[Literal["daily", "weekly", "monthly", "data", "voice", "sms"]] = None,
        auto_generate_token: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch available airtime and data plans from Sasai Wallet Payment Gateway.
        
        This wallet tool retrieves available mobile airtime, data, and bundle plans for different 
        providers that can be purchased using wallet funds.
        
        Args:
            provider: Mobile network provider (econet, netone, telecel)
            plan_type: Type of plan (daily, weekly, monthly, data, voice, sms)
            auto_generate_token: Whether to automatically generate a new token if none exists
        
        Returns:
            dict: Wallet airtime plans information including:
                - plans: List of available plans with pricing for wallet purchases
                - providers: Available providers for wallet transactions
                - plan_categories: Available plan types for wallet purchases
        
        Raises:
            AuthenticationError: If authentication is required but token is missing
            SasaiAPIError: If the API request fails or returns an error
        """
        # Check if we need to generate a token
        if not token_manager.has_token() and auto_generate_token:
            token_result = await generate_authentication_token()
            if not token_result.get("success"):
                raise Exception("Failed to generate authentication token")
        
        # Prepare query parameters
        params = {}
        if provider:
            params["provider"] = provider
        if plan_type:
            params["planType"] = plan_type
        
        # Make the API request using the API client
        client = SasaiAPIClient()
        result = await client.get(
            endpoint=SasaiConfig.ENDPOINTS.airtime_plans,
            token=token_manager.get_token(),
            params=params,
            require_auth=True
        )
        
        # Enhance response with request metadata
        result["request_info"] = {
            "provider_filter": provider,
            "plan_type_filter": plan_type,
            "tool": "get_wallet_airtime_plans"
        }
        
        return result
