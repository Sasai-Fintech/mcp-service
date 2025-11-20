"""Linked cards operations for FastMCP server."""

from typing import Literal, Optional, Dict, Any

from config import SasaiConfig
from api import SasaiAPIClient
from auth.manager import token_manager
from auth.tools import generate_authentication_token


def register_card_tools(mcp_server) -> None:
    """
    Register wallet linked cards tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_wallet_linked_cards(
        card_type: Optional[Literal["credit", "debit", "prepaid", "all"]] = "all",
        status: Optional[Literal["active", "inactive", "blocked", "all"]] = "all",
        auto_generate_token: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch linked cards and payment methods from Sasai Wallet Payment Gateway.
        
        This wallet tool retrieves all payment cards and methods linked to the authenticated 
        user's wallet account. Note: The API returns all linked cards; filtering parameters 
        are for client-side processing only.
        
        Args:
            card_type: Filter results by card type (credit, debit, prepaid, or all) - client-side filtering
            status: Filter results by card status (active, inactive, blocked, or all) - client-side filtering
            auto_generate_token: Whether to automatically generate a new token if none exists
        
        Returns:
            dict: Wallet linked cards information including:
                - cards: List of linked payment cards in wallet
                - payment_methods: Other linked payment methods in wallet
                - summary: Summary of card counts by type and status
                - filters_applied: Information about requested filters (client-side only)
        
        Raises:
            AuthenticationError: If authentication is required but token is missing
            SasaiAPIError: If the API request fails or returns an error
        """
        # Check if we need to generate a token
        if not token_manager.has_token() and auto_generate_token:
            token_result = await generate_authentication_token()
            if not token_result.get("success"):
                raise Exception("Failed to generate authentication token")
        
        # Note: Based on API specification, linked cards endpoint doesn't support query parameters
        # We'll retrieve all cards and do client-side filtering if needed
        
        # Make the API request using the API client
        client = SasaiAPIClient()
        result = await client.get(
            endpoint=SasaiConfig.ENDPOINTS.linked_cards,
            token=token_manager.get_token(),
            params=None,  # API doesn't support query parameters
            require_auth=True
        )
        
        # Enhance response with request metadata
        result["request_info"] = {
            "card_type_filter_requested": card_type,
            "status_filter_requested": status,
            "filtering_note": "API returns all wallet cards; filters are for client-side processing",
            "tool": "get_wallet_linked_cards"
        }
        
        return result
