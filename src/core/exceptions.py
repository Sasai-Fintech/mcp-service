"""Custom exceptions for the FastMCP Sasai server."""

from fastmcp.exceptions import ToolError


class SasaiAPIError(ToolError):
    """Base exception for Sasai API related errors."""
    
    def __init__(self, message: str, status_code: int = None, endpoint: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint


class AuthenticationError(SasaiAPIError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, **kwargs)


class TokenExpiredError(AuthenticationError):
    """Raised when the authentication token has expired."""
    
    def __init__(self, message: str = "Authentication token has expired", **kwargs):
        super().__init__(message, **kwargs)


class APITimeoutError(SasaiAPIError):
    """Raised when API requests timeout."""
    
    def __init__(self, message: str = "API request timed out", timeout: float = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout = timeout


class NetworkError(SasaiAPIError):
    """Raised when network connectivity issues occur."""
    
    def __init__(self, message: str = "Network connectivity error", **kwargs):
        super().__init__(message, **kwargs)


class ValidationError(SasaiAPIError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str = "Request validation failed", field: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field


class RateLimitError(SasaiAPIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(SasaiAPIError):
    """Raised when the Sasai server returns a server error (5xx)."""
    
    def __init__(self, message: str = "Server error occurred", **kwargs):
        super().__init__(message, **kwargs)
