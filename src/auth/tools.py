"""Authentication tools for FastMCP server."""

import httpx
from typing import Dict, Any

from config.settings import SasaiConfig
from core.exceptions import SasaiAPIError, AuthenticationError, APITimeoutError, NetworkError
from auth.manager import token_manager


async def generate_authentication_token() -> Dict[str, Any]:
    """
    Generate authentication token for Sasai Payment Gateway.
    
    This function implements the complete authentication flow:
    1. Login with credentials to get initial access token
    2. Verify PIN with the access token  
    3. If PIN verification fails, refresh the token
    4. Return the final valid access token
    
    Returns:
        dict: Token generation result with success status and token details
    
    Raises:
        AuthenticationError: If authentication flow fails at any step
        APITimeoutError: If the request times out
        NetworkError: If network connectivity issues occur
        SasaiAPIError: For other API-related errors
    """
    try:
        # Step 1: Initial login to get access token
        login_payload = {
            "username": SasaiConfig.AUTH_CREDENTIALS.username,
            "password": SasaiConfig.AUTH_CREDENTIALS.password,
            "tenantId": SasaiConfig.TENANT_ID,
            "clientId": SasaiConfig.CLIENT_ID
        }
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # Make login request
            headers = SasaiConfig.DEFAULT_HEADERS.copy()
            headers.update({
                "currentVersion": "1.1.0"
            })
            
            login_response = await client.post(
                SasaiConfig.ENDPOINTS.login,
                json=login_payload,
                headers=headers
            )
            
            if login_response.status_code != 200:
                raise AuthenticationError(
                    f"Login failed with status {login_response.status_code}: {login_response.text}"
                )
            
            login_data = login_response.json()
            guest_token = login_data.get("accessToken")
            login_refresh_token = login_data.get("refreshToken")
            
            if not guest_token:
                raise AuthenticationError("No guest token received from login")

            # Step 2: Verify PIN with guest token
            pin_verify_url = f"{SasaiConfig.ENDPOINTS.pin_verify}?tenantId={SasaiConfig.TENANT_ID}&azp={SasaiConfig.CLIENT_ID}"
            pin_payload = {
                "pin": SasaiConfig.AUTH_CREDENTIALS.pin,
                "userReferenceId": SasaiConfig.AUTH_CREDENTIALS.user_reference_id
            }
            
            pin_headers = SasaiConfig.DEFAULT_HEADERS.copy()
            pin_headers.update({
                "os": "ios",
                "Authorization": f"Bearer {guest_token}"
            })
            
            pin_response = await client.post(
                pin_verify_url,
                json=pin_payload,
                headers=pin_headers
            )
            
            # Step 3: Check PIN verification result
            if pin_response.status_code == 200:
                # PIN verification successful, use this token
                pin_data = pin_response.json()
                final_token = pin_data.get("accessToken")
                refresh_token = pin_data.get("refreshToken")
                
                if not final_token:
                    raise AuthenticationError("No access token in PIN verification response")
                
                # Store token with metadata
                token_metadata = {
                    "source": "pin_verification",
                    "expires_info": login_data.get("expiresIn", "Unknown"),
                    "refresh_token": refresh_token
                }
                token_manager.set_token(final_token, token_metadata)
                
                return {
                    "success": True,
                    "message": "Token generated successfully via PIN verification",
                    "token_source": "pin_verification",
                    "token": final_token,
                    "expires_info": login_data.get("expiresIn", "Unknown")
                }
            
            # Step 4: PIN verification failed, try refresh token
            elif login_refresh_token:
                refresh_url = f"{SasaiConfig.ENDPOINTS.refresh_token}?refreshToken={login_refresh_token}&tenantId={SasaiConfig.TENANT_ID}&azp={SasaiConfig.CLIENT_ID}"
                
                refresh_headers = SasaiConfig.DEFAULT_HEADERS.copy()
                refresh_headers.update({
                    "appVersion": "1.3.2",
                    "Authorization": f"Bearer {guest_token}"
                })
                
                refresh_response = await client.post(
                    refresh_url,
                    headers=refresh_headers
                )
                
                if refresh_response.status_code == 200:
                    refresh_data = refresh_response.json()
                    final_token = refresh_data.get("accessToken")
                    
                    if not final_token:
                        raise AuthenticationError("No access token in refresh response")
                    
                    # Store token with metadata
                    token_metadata = {
                        "source": "refresh_token",
                        "pin_verification_failed": True,
                        "pin_error": pin_response.text
                    }
                    token_manager.set_token(final_token, token_metadata)
                    
                    return {
                        "success": True,
                        "message": "Token generated successfully via refresh token",
                        "token_source": "refresh_token",
                        "token": final_token,
                        "pin_verification_failed": True,
                        "pin_error": pin_response.text
                    }
                else:
                    raise AuthenticationError(
                        f"Token refresh failed: {refresh_response.status_code} - {refresh_response.text}"
                    )
            else:
                raise AuthenticationError(
                    f"PIN verification failed and no refresh token available. PIN error: {pin_response.text}"
                )
            
    except httpx.TimeoutException:
        raise APITimeoutError(
            "Token generation timeout: Authentication servers did not respond within 30 seconds"
        )
    except httpx.NetworkError as e:
        raise NetworkError(f"Network error during token generation: {str(e)}")
    except Exception as e:
        if isinstance(e, SasaiAPIError):
            raise
        raise SasaiAPIError(f"Unexpected error during token generation: {str(e)}")


def register_auth_tools(mcp_server) -> None:
    """
    Register wallet authentication tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def generate_wallet_authentication_token() -> Dict[str, Any]:
        """
        Generate authentication token for Sasai Wallet Payment Gateway API.
        
        This wallet authentication tool implements the complete authentication flow:
        1. Login with credentials to get initial access token for wallet operations
        2. Verify PIN with the access token for wallet authentication
        3. If PIN verification fails, refresh the token
        4. Return the final valid access token for wallet access
        
        Returns:
            dict: Wallet token generation result with success status and token details
        
        Raises:
            AuthenticationError: If wallet authentication flow fails at any step
        """
        return await generate_authentication_token()
    
    @mcp_server.tool
    async def get_wallet_token_status() -> Dict[str, Any]:
        """
        Check the current wallet authentication token status.
        
        Returns:
            dict: Information about the current wallet token including availability and preview
        """
        return token_manager.get_token_status()
    
    @mcp_server.tool
    async def clear_wallet_token() -> Dict[str, Any]:
        """
        Clear the current wallet authentication token.
        
        This is useful when you want to force a fresh wallet token generation.
        
        Returns:
            dict: Status of the wallet token clearing operation
        """
        had_token = token_manager.clear_token()
        
        return {
            "success": True,
            "message": "Wallet token cleared successfully" if had_token else "No wallet token was present",
            "had_token_before": had_token
        }
