"""Customer profile operations for FastMCP server."""

from typing import Dict, Any

from config import SasaiConfig
from api import SasaiAPIClient
from auth.manager import token_manager
from auth.tools import generate_authentication_token


def register_profile_tools(mcp_server) -> None:
    """
    Register wallet customer profile tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_wallet_customer_profile(
        include_preferences: bool = True,
        include_verification_status: bool = True,
        auto_generate_token: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch wallet customer profile information from Sasai Payment Gateway.
        
        This wallet tool retrieves the authenticated user's wallet profile information including 
        personal details, verification status, and account preferences for wallet operations.
        
        Args:
            include_preferences: Whether to include wallet user preferences in the response
            include_verification_status: Whether to include wallet account verification status
            auto_generate_token: Whether to automatically generate a new token if none exists
        
        Returns:
            dict: Wallet customer profile information including:
                - personal_info: Basic personal information for wallet account
                - contact_details: Phone, email, address information for wallet
                - verification_status: Wallet account verification details (if requested)
                - preferences: Wallet user preferences and settings (if requested)
                - account_summary: Wallet account status and summary
        
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
        if include_preferences:
            params["includePreferences"] = "true"
        if include_verification_status:
            params["includeVerificationStatus"] = "true"
        
        # Make the API request using the API client
        client = SasaiAPIClient()
        result = await client.get(
            endpoint=SasaiConfig.ENDPOINTS.customer_profile,
            token=token_manager.get_token(),
            params=params,
            require_auth=True
        )
        
        # Enhance response with request metadata
        result["request_info"] = {
            "include_preferences": include_preferences,
            "include_verification_status": include_verification_status,
            "tool": "get_wallet_customer_profile"
        }
        
        return result
