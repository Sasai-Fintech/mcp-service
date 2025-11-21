"""HTTP client for Sasai Payment Gateway API."""

import httpx
from typing import Dict, Any, Optional

from config.settings import SasaiConfig
from core.exceptions import (
    SasaiAPIError,
    AuthenticationError,
    TokenExpiredError,
    APITimeoutError,
    NetworkError,
    ValidationError,
    RateLimitError,
    ServerError
)


class SasaiAPIClient:
    """HTTP client wrapper for Sasai Payment Gateway API calls."""
    
    def __init__(self):
        """Initialize the API client."""
        self._timeout = httpx.Timeout(SasaiConfig.REQUEST_TIMEOUT)
    
    async def make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        token: Optional[str] = None,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        require_auth: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[Any, Any]:
        """
        Make an authenticated HTTP request to the Sasai Payment Gateway.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint URL
            token: Authentication token
            params: Query parameters
            json_data: JSON payload for POST requests
            require_auth: Whether authentication token is required
            timeout: Request timeout in seconds (overrides default)
            
        Returns:
            dict: API response data
            
        Raises:
            AuthenticationError: If authentication is required but token is missing
            TokenExpiredError: If the authentication token has expired
            ValidationError: If request validation fails
            APITimeoutError: If the request times out
            NetworkError: If network connectivity issues occur
            RateLimitError: If API rate limits are exceeded
            ServerError: If the server returns a server error
            SasaiAPIError: For other API-related errors
        """
        # Check authentication requirement
        if require_auth and not token:
            raise AuthenticationError("Authentication token required. Please call generate_token first.")
        
        # Prepare headers
        headers = SasaiConfig.DEFAULT_HEADERS.copy()
        if token and require_auth:
            headers["Authorization"] = f"Bearer {token}"
        
        # Use custom timeout if provided
        request_timeout = httpx.Timeout(timeout) if timeout else self._timeout
        
        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                # Make the appropriate HTTP request
                if method.upper() == "GET":
                    response = await client.get(endpoint, params=params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(endpoint, params=params, json=json_data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(endpoint, params=params, json=json_data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(endpoint, params=params, headers=headers)
                elif method.upper() == "PATCH":
                    response = await client.patch(endpoint, params=params, json=json_data, headers=headers)
                else:
                    raise ValidationError(f"Unsupported HTTP method: {method}")
                
                return self._handle_response(response, endpoint)
                    
        except httpx.TimeoutException:
            timeout_value = timeout or SasaiConfig.REQUEST_TIMEOUT
            raise APITimeoutError(
                f"Request timeout: API did not respond within {timeout_value} seconds",
                timeout=timeout_value,
                endpoint=endpoint
            )
        except httpx.NetworkError as e:
            raise NetworkError(
                f"Network error: Unable to connect to payment gateway - {str(e)}",
                endpoint=endpoint
            )
        except Exception as e:
            # Re-raise our custom exceptions
            if isinstance(e, SasaiAPIError):
                raise
            # Wrap unexpected errors
            raise SasaiAPIError(f"Unexpected error during API request: {str(e)}", endpoint=endpoint)
    
    def _handle_response(self, response: httpx.Response, endpoint: str) -> Dict[Any, Any]:
        """
        Handle HTTP response and convert to appropriate exceptions.
        
        Args:
            response: HTTP response object
            endpoint: API endpoint that was called
            
        Returns:
            dict: Processed response data
            
        Raises:
            Various SasaiAPIError subclasses based on response status
        """
        # Success response - handle all 2xx status codes
        if 200 <= response.status_code < 300:
            # Handle empty body responses (e.g., 204 No Content)
            if not response.text.strip():
                response_data = None
            else:
                try:
                    response_data = response.json()
                except (ValueError, Exception):
                    # Fallback for non-JSON responses
                    response_data = {"message": response.text}
            
            return {
                "success": True,
                "data": response_data,
                "status_code": response.status_code,
                "endpoint": str(response.url)
            }
        
        # Handle different error status codes
        elif response.status_code == 401:
            raise TokenExpiredError(
                "Authentication failed. Token may be expired. Please call generate_token again.",
                status_code=response.status_code,
                endpoint=endpoint
            )
        
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("message", "Bad request")
                field = error_data.get("field")
            except:
                error_message = response.text or "Bad request"
                field = None
            
            raise ValidationError(
                f"Bad request: {error_message}",
                status_code=response.status_code,
                endpoint=endpoint,
                field=field
            )
        
        elif response.status_code == 404:
            raise SasaiAPIError(
                f"API endpoint not found: {endpoint}",
                status_code=response.status_code,
                endpoint=endpoint
            )
        
        elif response.status_code == 429:
            # Extract retry-after header if available
            retry_after = None
            if "retry-after" in response.headers:
                try:
                    retry_after = int(response.headers["retry-after"])
                except ValueError:
                    pass
            
            raise RateLimitError(
                "Rate limit exceeded. Please wait before making more requests.",
                status_code=response.status_code,
                endpoint=endpoint,
                retry_after=retry_after
            )
        
        elif response.status_code >= 500:
            raise ServerError(
                f"Server error: Payment gateway is experiencing issues (Status: {response.status_code})",
                status_code=response.status_code,
                endpoint=endpoint
            )
        
        else:
            # Handle other error codes
            try:
                error_data = response.json()
                error_message = error_data.get("message", f"HTTP {response.status_code}")
            except:
                error_message = f"HTTP {response.status_code}"
            
            raise SasaiAPIError(
                f"API request failed: {error_message}",
                status_code=response.status_code,
                endpoint=endpoint
            )
    
    async def get(self, endpoint: str, token: Optional[str] = None, **kwargs) -> Dict[Any, Any]:
        """Make a GET request."""
        return await self.make_authenticated_request("GET", endpoint, token=token, **kwargs)
    
    async def post(self, endpoint: str, token: Optional[str] = None, **kwargs) -> Dict[Any, Any]:
        """Make a POST request."""
        return await self.make_authenticated_request("POST", endpoint, token=token, **kwargs)
    
    async def put(self, endpoint: str, token: Optional[str] = None, **kwargs) -> Dict[Any, Any]:
        """Make a PUT request."""
        return await self.make_authenticated_request("PUT", endpoint, token=token, **kwargs)
    
    async def delete(self, endpoint: str, token: Optional[str] = None, **kwargs) -> Dict[Any, Any]:
        """Make a DELETE request."""
        return await self.make_authenticated_request("DELETE", endpoint, token=token, **kwargs)
    
    async def patch(self, endpoint: str, token: Optional[str] = None, **kwargs) -> Dict[Any, Any]:
        """Make a PATCH request."""
        return await self.make_authenticated_request("PATCH", endpoint, token=token, **kwargs)
