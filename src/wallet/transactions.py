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
            "pin": SasaiConfig.get_auth_credentials().pin,  # PIN is required for transaction history
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

    @mcp_server.tool
    async def get_transaction_details(user_id: str, transaction_id: str = "") -> Dict[str, Any]:
        """Get detailed information about a specific transaction.
        
        This helps provide a summary when user asks for help with a transaction.
        If transaction_id is provided, fetch that specific transaction.
        If not provided, returns the most recent transaction.
        Returns transaction details including merchant, date, amount, status, and UTR/reference number.
        """
        # In a real implementation, we would have a specific endpoint for transaction details
        # For now, we can reuse the history endpoint to find the transaction
        
        # Check if we need to generate a token
        if not token_manager.has_token():
            token_result = await generate_authentication_token()
            if not token_result.get("success"):
                raise Exception("Failed to generate authentication token")
        
        # Prepare JSON payload for history
        # We fetch the first page to find the transaction or get the latest one
        json_payload = {
            "pin": SasaiConfig.get_auth_credentials().pin,
            "currency": "USD", # Default to USD for now, or could be an argument
            "page": 0,
            "pageSize": 20
        }
        
        # Make the API request using the API client
        client = SasaiAPIClient()
        result = await client.post(
            endpoint=SasaiConfig.ENDPOINTS.transaction_history,
            token=token_manager.get_token(),
            json_data=json_payload,
            require_auth=True
        )
        
        transactions = result.get("transactions", [])
        
        # Find transaction by ID if provided
        if transaction_id:
            # Note: The real API might use different ID fields, adjusting to match
            transaction = next((t for t in transactions if t.get("id") == transaction_id or t.get("transactionId") == transaction_id), None)
            if transaction:
                return transaction
        
        # Return most recent transaction (first in list) as fallback
        return transactions[0] if transactions else {}

