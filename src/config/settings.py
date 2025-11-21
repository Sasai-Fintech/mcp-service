"""Configuration module for Sasai Payment Gateway API."""

import os
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
    
    # Authentication credentials (from environment variables for security)
    AUTH_CREDENTIALS = AuthCredentials(
        username=os.getenv("SASAI_USERNAME", "64543532-3dee-43bc-b42e-d6b503f7fbdb"),
        password=os.getenv("SASAI_PASSWORD", "iW8I*0bZ"),
        pin=os.getenv("SASAI_PIN", "OcXNch0pf3OKT+SD9xpM3qVoL6sDV2boAVWQjPj4H1+9VJhg4GyBsqC8Hu/x06YA50wxknXQqlIF5BFnd98zALxZOCX1i+xoPHuXdNn2Xqai/rBBeQf4N5Bq3r0JoOoyWUO954T4/3Ax2K57flYn0vntFglo8gJGfSSvPk8PJaCaVHDWir3VFfGJ2/vR59gqt7C+QeMkEMIhba89KGdHmSybdzZ7DjW7T4IjIkVIcpOTD/KhWGLovRuO7ptMI8u5gXp9ut/ZK+4PnD17N0XNxYXZXVk4SHbp784Sl3lKbpAwE5YZEP79rmAt723xJuz/KEPatOocyFN7sV2j/C+WVg=="),
        user_reference_id=os.getenv("SASAI_USER_REFERENCE_ID", "8da526ff-3813-466d-9aed-6fc9cdc72931")
    )
    
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
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
        
        # Validate URLs
        try:
            import urllib.parse
            parsed_url = urllib.parse.urlparse(cls.BASE_URL)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                issues.append(f"Invalid base URL: {cls.BASE_URL}")
        except Exception as e:
            issues.append(f"URL validation error: {str(e)}")
        
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
