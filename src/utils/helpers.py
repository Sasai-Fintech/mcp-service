"""Utility functions for the FastMCP server."""

import os
import logging
from typing import Dict, Any, Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format string
        log_file: Optional log file path
    
    Returns:
        logging.Logger: Configured logger instance
    """
    log_format = format_string or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        filename=log_file,
        filemode="a" if log_file else None
    )
    
    logger = logging.getLogger("sasai-wallet-server")
    return logger


def load_environment_variables() -> Dict[str, Any]:
    """
    Load and validate environment variables.
    
    Returns:
        dict: Dictionary containing environment variable status
    """
    required_vars = [
        "SASAI_USERNAME",
        "SASAI_PASSWORD", 
        "SASAI_PIN",
        "SASAI_USER_REFERENCE_ID"
    ]
    
    optional_vars = [
        "SASAI_ENVIRONMENT",
        "SASAI_CLIENT_ID",
        "SASAI_TENANT_ID",
        "REQUEST_TIMEOUT",
        "MAX_RETRIES",
        "LOG_LEVEL",
        "SERVER_VERSION"
    ]
    
    loaded_vars = {}
    missing_vars = []
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            loaded_vars[var] = "***" if "password" in var.lower() or "pin" in var.lower() else value[:10] + "..."
        else:
            missing_vars.append(var)
    
    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            loaded_vars[var] = value
    
    return {
        "loaded_variables": loaded_vars,
        "missing_required": missing_vars,
        "all_required_present": len(missing_vars) == 0,
        "total_loaded": len(loaded_vars),
        "status": "complete" if len(missing_vars) == 0 else "incomplete"
    }


def format_api_response(
    response_data: Dict[str, Any],
    tool_name: str,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Format API response with consistent structure.
    
    Args:
        response_data: Raw API response data
        tool_name: Name of the tool that made the request
        include_metadata: Whether to include metadata in the response
    
    Returns:
        dict: Formatted response data
    """
    formatted_response = {
        "success": response_data.get("success", True),
        "data": response_data.get("data", {}),
        "status_code": response_data.get("status_code")
    }
    
    if include_metadata:
        formatted_response["metadata"] = {
            "tool": tool_name,
            "endpoint": response_data.get("endpoint"),
            "timestamp": response_data.get("timestamp"),
            "request_info": response_data.get("request_info", {})
        }
    
    return formatted_response


def validate_pagination_params(page: int, page_size: int, max_page_size: int = 100) -> Dict[str, Any]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (0-based)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size
    
    Returns:
        dict: Validation result with status and any errors
    """
    errors = []
    
    if page < 0:
        errors.append("Page number must be non-negative")
    
    if page_size < 1:
        errors.append("Page size must be at least 1")
    elif page_size > max_page_size:
        errors.append(f"Page size must not exceed {max_page_size}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "normalized_params": {
            "page": max(0, page),
            "page_size": min(max(1, page_size), max_page_size)
        }
    }


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: Optional[list] = None) -> Dict[str, Any]:
    """
    Mask sensitive data in dictionaries for logging.
    
    Args:
        data: Dictionary that may contain sensitive data
        sensitive_keys: List of keys to mask (defaults to common sensitive keys)
    
    Returns:
        dict: Dictionary with sensitive values masked
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "password", "pin", "token", "secret", "key", "auth", "authorization",
            "credential", "access_token", "refresh_token", "api_key"
        ]
    
    masked_data = data.copy()
    
    for key, value in masked_data.items():
        key_lower = key.lower()
        
        # Check if key contains any sensitive terms
        is_sensitive = any(sensitive_term in key_lower for sensitive_term in sensitive_keys)
        
        if is_sensitive and isinstance(value, str) and len(value) > 0:
            # Mask all but first 3 and last 3 characters
            if len(value) <= 6:
                masked_data[key] = "***"
            else:
                masked_data[key] = value[:3] + "*" * (len(value) - 6) + value[-3:]
        elif isinstance(value, dict):
            # Recursively mask nested dictionaries
            masked_data[key] = mask_sensitive_data(value, sensitive_keys)
    
    return masked_data


def create_error_response(
    error_message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        error_message: Human-readable error message
        error_code: Optional error code for programmatic handling
        details: Optional additional error details
    
    Returns:
        dict: Standardized error response
    """
    error_response = {
        "success": False,
        "error": {
            "message": error_message,
            "code": error_code,
            "details": details or {}
        }
    }
    
    return error_response
