"""Transaction history operations for FastMCP server."""

from typing import Literal, Dict, Any

from config import SasaiConfig
from api import SasaiAPIClient
from auth.manager import token_manager
from auth.tools import generate_authentication_token
from core.exceptions import ValidationError


def register_transaction_tools(mcp_server) -> None:
    """
    Register wallet transaction history tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_wallet_transaction_history(
        page: int = 0,
        pageSize: int = 20,
        currency: Literal["USD", "EUR", "GBP", "ZWL"] = "USD",
        auto_generate_token: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch wallet transaction history from Sasai Payment Gateway.
        
        This wallet tool retrieves the transaction history for the authenticated user's wallet.
        The API requires a POST request with PIN verification and pagination parameters.
        
        Args:
            page: Page number for pagination (0-based)
            pageSize: Number of transactions per page (1-100)
            currency: Currency for wallet transaction history (USD, EUR, GBP, ZWL)
            auto_generate_token: Whether to automatically generate a new token if none exists
        
        Returns:
            dict: Wallet transaction history including:
                - transactions: List of wallet transaction records
                - pagination: Pagination information
                - currency: Currency filter applied
                - total_count: Total number of wallet transactions
        
        Raises:
            ValidationError: If parameters are invalid
            AuthenticationError: If authentication is required but token is missing
            SasaiAPIError: If the API request fails or returns an error
        """
        # Validate parameters
        if pageSize < 1 or pageSize > 100:
            raise ValidationError("Page size must be between 1 and 100", field="pageSize")
        if page < 0:
            raise ValidationError("Page must be non-negative", field="page")
        
        # Check if we need to generate a token
        if not token_manager.has_token() and auto_generate_token:
            token_result = await generate_authentication_token()
            if not token_result.get("success"):
                raise Exception("Failed to generate authentication token")
        
        # Prepare JSON payload (as required by the API)
        json_payload = {
            "pin": SasaiConfig.AUTH_CREDENTIALS.pin,  # PIN is required for transaction history
            "currency": currency,
            "page": page,
            "pageSize": pageSize
        }
        
        # Make the API request using the API client
        client = SasaiAPIClient()
        result = await client.post(
            endpoint=SasaiConfig.ENDPOINTS.transaction_history,
            token=token_manager.get_token(),
            json_data=json_payload,
            require_auth=True
        )
        
        # Enhance response with request metadata
        result["request_info"] = {
            "page": page,
            "pageSize": pageSize,
            "currency": currency,
            "tool": "get_wallet_transaction_history"
        }
        
        return result
