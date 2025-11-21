"""Token management for Sasai Payment Gateway authentication."""

from typing import Optional, Dict, Any


class TokenManager:
    """Manages authentication tokens for the Sasai Payment Gateway."""
    
    def __init__(self):
        """Initialize the token manager."""
        self._current_token: Optional[str] = None
        self._token_metadata: Dict[str, Any] = {}
    
    def set_token(self, token: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set the current authentication token.
        
        Args:
            token: The authentication token
            metadata: Optional metadata about the token (e.g., expiry, source)
        """
        self._current_token = token
        self._token_metadata = metadata or {}
    
    def get_token(self) -> Optional[str]:
        """
        Get the current authentication token.
        
        Returns:
            str or None: Current authentication token if available
        """
        return self._current_token
    
    def get_token_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the current token.
        
        Returns:
            dict: Token metadata
        """
        return self._token_metadata.copy()
    
    def has_token(self) -> bool:
        """
        Check if a token is currently available.
        
        Returns:
            bool: True if token is available, False otherwise
        """
        return self._current_token is not None
    
    def clear_token(self) -> bool:
        """
        Clear the current authentication token.
        
        Returns:
            bool: True if a token was cleared, False if no token was present
        """
        had_token = self._current_token is not None
        self._current_token = None
        self._token_metadata = {}
        return had_token
    
    def get_token_status(self) -> Dict[str, Any]:
        """
        Get comprehensive token status information.
        
        Returns:
            dict: Token status information
        """
        return {
            "token_available": self.has_token(),
            "token_preview": self._current_token[:20] + "..." if self._current_token else None,
            "token_length": len(self._current_token) if self._current_token else 0,
            "metadata": self._token_metadata.copy(),
            "recommendation": "Token is available" if self.has_token() else "Call generate_token to authenticate"
        }


# Global token manager instance
token_manager = TokenManager()
