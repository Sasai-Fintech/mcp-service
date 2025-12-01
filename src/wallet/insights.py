"""Financial insights operations for FastMCP server."""

from typing import Dict, Any, List
from datetime import datetime

def register_insights_tools(mcp_server) -> None:
    """
    Register wallet insights tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_incoming_insights(
        user_id: str,
        account: str = "all accounts",
        start_date: str = "",
        end_date: str = ""
    ) -> Dict[str, Any]:
        """Get financial insights for incoming transactions.
        
        Returns insights including total amount, categories with percentages, and subcategories.
        Categories include: others, reversal_and_refunds, dividend, people, etc.
        """
        # Default to current month if dates not provided
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Dummy data based on screenshots
        return {
            "category": "incoming",
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "label": "6 MONTHS TOTAL"
            },
            "total_amount": 50000.0,
            "currency": "USD",
            "categories": [
                {
                    "name": "others",
                    "amount": 49665.0,
                    "percentage": 99.33,
                    "color": "#1e3a8a"  # Dark blue
                },
                {
                    "name": "reversal and refunds",
                    "amount": 300.0,
                    "percentage": 0.60,
                    "color": "#3b82f6"  # Medium blue
                },
                {
                    "name": "dividend",
                    "amount": 25.0,
                    "percentage": 0.05,
                    "color": "#60a5fa"  # Light blue
                },
                {
                    "name": "people",
                    "amount": 10.0,
                    "percentage": 0.02,
                    "color": "#93c5fd"  # Lightest blue
                }
            ]
        }

    @mcp_server.tool
    async def get_investment_insights(
        user_id: str,
        account: str = "all accounts",
        start_date: str = "",
        end_date: str = ""
    ) -> Dict[str, Any]:
        """Get financial insights for investment transactions.
        
        Returns insights including total amount, categories with percentages, and subcategories.
        """
        # Default to current month if dates not provided
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Dummy data
        return {
            "category": "investment",
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "label": "6 MONTHS TOTAL"
            },
            "total_amount": 15000.0,
            "currency": "USD",
            "categories": [
                {
                    "name": "stocks",
                    "amount": 9000.0,
                    "percentage": 60.0,
                    "color": "#059669"  # Green
                },
                {
                    "name": "mutual funds",
                    "amount": 4500.0,
                    "percentage": 30.0,
                    "color": "#10b981"
                },
                {
                    "name": "bonds",
                    "amount": 1500.0,
                    "percentage": 10.0,
                    "color": "#34d399"
                }
            ]
        }

    @mcp_server.tool
    async def get_cash_flow_overview(
        user_id: str,
        account: str = "all accounts",
        start_date: str = "",
        end_date: str = ""
    ) -> Dict[str, Any]:
        """Get overall cash flow overview with incoming, investment, and spends totals.
        
        Returns a summary with totals for each main category for displaying in a bar chart.
        """
        # Default to current month if dates not provided
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Dummy data - totals from individual insights
        return {
            "category": "overview",
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "label": "6 MONTHS TOTAL"
            },
            "currency": "USD",
            "categories": [
                {
                    "name": "Incoming",
                    "amount": 50000.0,
                    "color": "#3b82f6"  # Blue
                },
                {
                    "name": "Investment",
                    "amount": 15000.0,
                    "color": "#10b981"  # Green
                },
                {
                    "name": "Spends",
                    "amount": 12000.0,
                    "color": "#ef4444"  # Red
                }
            ]
        }

    @mcp_server.tool
    async def get_spends_insights(
        user_id: str,
        account: str = "all accounts",
        start_date: str = "",
        end_date: str = ""
    ) -> Dict[str, Any]:
        """Get financial insights for spending transactions.
        
        Returns insights including total amount, categories with percentages, and upcoming spends.
        Categories include: cash transactions, people, credit card bill, miscellaneous, etc.
        """
        # Default to current month if dates not provided
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Dummy data based on screenshots
        return {
            "category": "spends",
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "label": "6 MONTHS TOTAL"
            },
            "total_amount": 12000.0,
            "currency": "USD",
            "upcoming_spends": 500.0,
            "categories": [
                {
                    "name": "cash transactions",
                    "amount": 3700.8,
                    "percentage": 30.84,
                    "color": "#dc2626"  # Red
                },
                {
                    "name": "people",
                    "amount": 3513.6,
                    "percentage": 29.28,
                    "color": "#ef4444"
                },
                {
                    "name": "credit card bill",
                    "amount": 3121.2,
                    "percentage": 26.01,
                    "color": "#f87171"
                },
                {
                    "name": "miscellaneous",
                    "amount": 1665.6,
                    "percentage": 13.88,
                    "color": "#fca5a5"
                }
            ]
        }
