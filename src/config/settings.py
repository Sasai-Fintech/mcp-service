"""Configuration module for Sasai Payment Gateway API."""

import os
import sys
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class APIEndpoints:
    """API endpoint configuration."""
    login: str
    pin_verify: str
    refresh_token: str
    wallet_balance: str
    transaction_history: str
    linked_cards: str
    airtime_plans: str
    customer_profile: str


@dataclass
class AuthCredentials:
    """Authentication credentials configuration."""
    username: str
    password: str
    pin: str
    user_reference_id: str


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class SasaiConfig:
    """Configuration class for Sasai Payment Gateway."""
    
    # Environment settings
    ENVIRONMENT = os.getenv("SASAI_ENVIRONMENT", "sandbox")
    
    # Base URLs by environment
    BASE_URLS = {
        "sandbox": "https://sandbox.sasaipaymentgateway.com",
        "production": "https://api.sasaipaymentgateway.com"  # Example production URL
    }
    
    BASE_URL = BASE_URLS.get(ENVIRONMENT, BASE_URLS["sandbox"])
    
    # Client configuration
    CLIENT_ID = os.getenv("SASAI_CLIENT_ID", "sasai-pay-client")
    TENANT_ID = os.getenv("SASAI_TENANT_ID", "sasai")
    
    # API Endpoints
    ENDPOINTS = APIEndpoints(
        login=f"{BASE_URL}/bff/v2/auth/token",
        pin_verify=f"{BASE_URL}/bff/v4/auth/pin/verify",
        refresh_token=f"{BASE_URL}/bff/v3/user/refreshToken",
        wallet_balance=f"{BASE_URL}/bff/v1/wallet/profile/balance",
        transaction_history=f"{BASE_URL}/bff/v1/wallet/profile/transaction-history",
        linked_cards=f"{BASE_URL}/bff/v1/wallet/linked-cards",
        airtime_plans=f"{BASE_URL}/bff/v1/airtime/plans",
        customer_profile=f"{BASE_URL}/bff/v1/wallet/profile/cust-info",
    )
    
    # Default headers
    DEFAULT_HEADERS = {
        "deviceType": "ios",
        "Content-Type": "application/json",
        "User-Agent": f"FastMCP-SasaiWalletServer/{os.getenv('APP_VERSION', '2.0.0')}",
        "Accept": "application/json"
    }
    
    # Authentication credentials - REQUIRE environment variables for security
    @classmethod
    def _get_required_env(cls, var_name: str, description: str = None) -> str:
        """Get required environment variable or raise ConfigurationError."""
        value = os.getenv(var_name)
        if not value or value in ["CHANGE_ME", "your_value_here", ""]:
            error_msg = f"Required environment variable '{var_name}' is not set or contains placeholder value."
            if description:
                error_msg += f" {description}"
            raise ConfigurationError(error_msg)
        return value
    
    @classmethod
    def _get_auth_credentials(cls) -> AuthCredentials:
        """Get authentication credentials from environment variables."""
        try:
            return AuthCredentials(
                username=cls._get_required_env("SASAI_USERNAME", "Set your Sasai wallet username."),
                password=cls._get_required_env("SASAI_PASSWORD", "Set your Sasai wallet password."),
                pin=cls._get_required_env("SASAI_PIN", "Set your Sasai wallet PIN token."),
                user_reference_id=cls._get_required_env("SASAI_USER_REFERENCE_ID", "Set your Sasai user reference ID.")
            )
        except ConfigurationError as e:
            print(f"\n🚨 CONFIGURATION ERROR: {e}")
            print("\n📋 Required environment variables:")
            print("   - SASAI_USERNAME: Your Sasai wallet username")
            print("   - SASAI_PASSWORD: Your Sasai wallet password") 
            print("   - SASAI_PIN: Your Sasai wallet PIN token")
            print("   - SASAI_USER_REFERENCE_ID: Your Sasai user reference ID")
            print("\n💡 Set these in your environment or .env file before running the server.")
            print("   Example: export SASAI_USERNAME=your_username")
            sys.exit(1)
    
    # Initialize credentials with validation
    _AUTH_CREDENTIALS = None  # Will be set on first access
    
    @classmethod
    def get_auth_credentials(cls) -> AuthCredentials:
        """Get authentication credentials (lazy-loaded with validation)."""
        if cls._AUTH_CREDENTIALS is None:
            cls._AUTH_CREDENTIALS = cls._get_auth_credentials()
        return cls._AUTH_CREDENTIALS
    
    # HTTP client settings
    REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Server settings
    SERVER_NAME = os.getenv("SERVER_NAME", "SasaiWalletOperationsServer")
    SERVER_VERSION = os.getenv("SERVER_VERSION", "2.0.0")
    
    # Feature flags
    ENABLE_AUTO_TOKEN_REFRESH = os.getenv("ENABLE_AUTO_TOKEN_REFRESH", "true").lower() == "true"
    ENABLE_REQUEST_LOGGING = os.getenv("ENABLE_REQUEST_LOGGING", "false").lower() == "true"
    
    # RAG Service Configuration (Direct Retrieval API)
    RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8000/api/retriever")
    RAG_TENANT_ID = os.getenv("RAG_TENANT_ID", "sasai")
    RAG_TENANT_SUB_ID = os.getenv("RAG_TENANT_SUB_ID", "sasai-sub")
    RAG_KNOWLEDGE_BASE_ID = os.getenv("RAG_KNOWLEDGE_BASE_ID", "sasai-compliance-kb")
    RAG_PROVIDER_CONFIG_ID = os.getenv("RAG_PROVIDER_CONFIG_ID", "azure-openai-llm-gpt-4o-mini")
    RAG_REQUEST_TIMEOUT = float(os.getenv("RAG_REQUEST_TIMEOUT", "30.0"))
    
    @classmethod
    def get_server_instructions(cls) -> str:
        """Get comprehensive server instructions."""
        return f"""
        This server provides comprehensive wallet operations for the Sasai Payment Gateway.
        
        Environment: {cls.ENVIRONMENT}
        Base URL: {cls.BASE_URL}
        
        Authentication Flow:
        1. Use generate_token first to authenticate with the payment gateway
        2. All other tools automatically use the stored token
        
        Available Operations:
        - Wallet balance and profile management
        - Transaction history and details
        - Linked cards and payment methods
        - Airtime plans and mobile services
        - Customer profile information
        - Health monitoring and token management
        - Compliance knowledge and regulatory guidance (via RAG service)
        """
    
    @classmethod
    def validate_configuration(cls) -> Dict[str, Any]:
        """Validate current configuration and return status."""
        issues = []
        
        # Check required environment variables
        required_vars = [
            "SASAI_USERNAME", "SASAI_PASSWORD", "SASAI_PIN", "SASAI_USER_REFERENCE_ID"
        ]
        
        missing_vars = []
        placeholder_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif value in ["CHANGE_ME", "your_value_here", ""]:
                placeholder_vars.append(var)
        
        if missing_vars:
            issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
        if placeholder_vars:
            issues.append(f"Environment variables with placeholder values: {', '.join(placeholder_vars)}")
        
        # Validate URLs
        import urllib.parse
        parsed_url = urllib.parse.urlparse(cls.BASE_URL)
        if not parsed_url.scheme or not parsed_url.netloc:
            issues.append(f"Invalid base URL: {cls.BASE_URL}")
        
        # Validate timeout settings
        if cls.REQUEST_TIMEOUT <= 0:
            issues.append(f"Invalid request timeout: {cls.REQUEST_TIMEOUT}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "environment": cls.ENVIRONMENT,
            "base_url": cls.BASE_URL,
            "client_id": cls.CLIENT_ID,
            "tenant_id": cls.TENANT_ID
        }
