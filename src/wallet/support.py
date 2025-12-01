"""Support ticket operations for FastMCP server."""

import random
from typing import Dict, Any

def register_support_tools(mcp_server) -> None:
    """
    Register support ticket tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def create_ticket(user_id: str, subject: str, body: str) -> str:
        """Create a support ticket for the user.
        
        This will trigger a confirmation widget (human-in-the-loop) before creating the ticket.
        Returns a message with the ticket ID after confirmation.
        """
        # Placeholder – in a real system you'd call a ticketing service
        # The actual creation happens after user confirmation via the widget
        ticket_id = f"TICKET-{random.randint(10000, 99999)}"
        # Return message with ticket ID in a consistent format for easy parsing
        return f"Support ticket {ticket_id} created successfully. Our team will get back to you soon."
