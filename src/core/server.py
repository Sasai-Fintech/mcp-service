"""FastMCP server initialization and configuration."""

from fastmcp import FastMCP
from config.settings import SasaiConfig


def create_server() -> FastMCP:
    """
    Create and configure the FastMCP server instance.
    
    Returns:
        FastMCP: Configured server instance
    """
    return FastMCP(
        name=SasaiConfig.SERVER_NAME,
        instructions=SasaiConfig.get_server_instructions(),
        version=SasaiConfig.SERVER_VERSION
    )


def register_all_tools(mcp_server: FastMCP) -> None:
    """
    Register all tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance to register tools with
    """
    # Import all tool modules
    from auth.tools import register_auth_tools
    from wallet.balance import register_balance_tools
    from wallet.transactions import register_transaction_tools
    from wallet.cards import register_card_tools
    from wallet.airtime import register_airtime_tools
    from wallet.profile import register_profile_tools
    from monitoring.health import register_monitoring_tools
    from rag.tools import register_rag_tools
    from database.tools import register_database_tools
    from wallet.insights import register_insights_tools
    from wallet.support import register_support_tools
    
    # Register tools from each module
    register_auth_tools(mcp_server)
    register_balance_tools(mcp_server)
    register_transaction_tools(mcp_server)
    register_card_tools(mcp_server)
    register_airtime_tools(mcp_server)
    register_profile_tools(mcp_server)
    register_monitoring_tools(mcp_server)
    register_rag_tools(mcp_server)
    register_database_tools(mcp_server)
    register_insights_tools(mcp_server)
    register_support_tools(mcp_server)


def initialize_server() -> FastMCP:
    """
    Initialize the complete FastMCP server with all tools registered.
    
    Returns:
        FastMCP: Fully configured server instance
    """
    # Validate configuration
    config_status = SasaiConfig.validate_configuration()
    if not config_status["valid"]:
        print("⚠️ Configuration validation issues:")
        for issue in config_status["issues"]:
            print(f"  - {issue}")
        print("Server will continue but may not function correctly.")
    
    # Create server
    server = create_server()
    
    # Register all tools
    register_all_tools(server)
    
    return server
