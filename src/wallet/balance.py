"""Wallet balance operations for FastMCP server."""

from typing import Literal, Dict, Any

from config.settings import SasaiConfig
from api.client import SasaiAPIClient
from auth.manager import token_manager
from auth.tools import generate_authentication_token


def register_balance_tools(mcp_server) -> None:
    """
    Register wallet balance tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_wallet_balance(
        currency: Literal["USD", "EUR", "GBP", "ZWL"] = "USD",
        provider_code: Literal["ecocash", "onemoney", "telecash"] = "ecocash",
        auto_generate_token: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch wallet balance from Sasai Payment Gateway.
        
        This tool retrieves the current wallet balance for a specified currency and payment provider
        from the Sasai Payment Gateway sandbox environment.
        
        Args:
            currency: The currency code for the balance inquiry (USD, EUR, GBP, ZWL)
            provider_code: The payment provider code (ecocash, onemoney, telecash)
            auto_generate_token: Whether to automatically generate a new token if none exists
        
        Returns:
            dict: Wallet balance information including:
                - balance: Current balance amount
                - currency: Currency code
                - provider: Provider information
                - status: Transaction status
                - timestamp: Response timestamp
        
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
        params = {
            "currency": currency,
            "providerCode": provider_code
        }
        
        # Make the API request using the API client
        client = SasaiAPIClient()
        result = await client.get(
            endpoint=SasaiConfig.ENDPOINTS.wallet_balance,
            token=token_manager.get_token(),
            params=params,
            require_auth=True
        )
        
        # Enhance response with request metadata
        result["request_info"] = {
            "currency": currency,
            "provider_code": provider_code,
            "tool": "get_wallet_balance"
        }
        
        return result
