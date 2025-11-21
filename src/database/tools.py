"""
Database tools for MongoDB Orders analytics.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Literal, List

from core.exceptions import SasaiAPIError
from .client import DatabaseClient, db_client, get_customer_context


def register_database_tools(mcp_server) -> None:
    """
    Register database analytics tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def get_order_analytics(
        customer_id: Optional[str] = None,
        analysis_period_days: int = 30,
        order_type: Optional[str] = None,
        currency: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive order analytics from the database.
        
        This tool analyzes order data from the payment service database to provide insights
        about transaction volumes, amounts, fees, and patterns.
        
        Args:
            customer_id: Optional customer ID to filter orders for specific customer
            analysis_period_days: Number of days to analyze (default: 30)
            order_type: Optional filter by order type (e.g., 'fund_transfer', 'bill_payment')
            currency: Optional filter by currency (e.g., 'USD', 'ZWL')
            auth_token: JWT authentication token (automatically extracts customer_id and country)
        
        Returns:
            dict: Order analytics including:
                - total_orders: Total number of orders in period
                - total_amount: Sum of all order amounts
                - total_fees: Sum of all fees collected
                - average_amount: Average order amount
                - max_amount: Largest single order
                - min_amount: Smallest single order
                - order_types: Types of orders found
                - currencies: Currencies used
                - statuses: Order statuses found
                - customer_context: Info about authenticated customer (if token provided)
        
        Raises:
            SasaiAPIError: If database query fails
        """
        try:
            # Ensure database connection
            await db_client.connect()
            
            # Get order analytics with authentication context
            analytics = await db_client.get_order_analytics(
                customer_id=customer_id,
                days=analysis_period_days,
                order_type=order_type,
                currency=currency,
                auth_token=auth_token
            )
            
            # Extract customer context for response metadata
            customer_context = get_customer_context(auth_token)
            
            # Enhance result with metadata
            result = {
                "success": True,
                "analytics": analytics,
                "filters_applied": {
                    "customer_id": customer_id or customer_context.get("customer_id"),
                    "analysis_period_days": analysis_period_days,
                    "order_type": order_type,
                    "currency": currency,
                    "authenticated_user": bool(auth_token and customer_context.get("customer_id"))
                },
                "request_info": {
                    "tool": "get_order_analytics",
                    "analysis_date": datetime.utcnow().isoformat(),
                    "data_source": "payment_service_orders",
                    "user_context": customer_context.get("country_code") if customer_context else None
                }
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to get order analytics: {str(e)}")
    
    @mcp_server.tool
    async def analyze_customer_spending_patterns(
        customer_id: str,
        analysis_period_days: int = 30,
        group_by: Literal["day", "week", "month"] = "day",
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze spending patterns for a specific customer over time.
        
        This tool examines how a customer's order behavior changes over time,
        identifying trends in spending frequency and amounts.
        
        Args:
            customer_id: The customer ID to analyze
            analysis_period_days: Number of days to analyze
            group_by: How to group the time analysis (day, week, month)
        
        Returns:
            dict: Customer spending pattern analysis including:
                - time_periods: Order data grouped by time period
                - trends: Identified trends in customer behavior
                - customer_summary: Overall customer statistics
                - recommendations: Insights about customer behavior
        
        Raises:
            SasaiAPIError: If analysis fails or customer not found
        """
        try:
            # Ensure database connection
            await db_client.connect()
            
            # Get customer-specific order analytics
            customer_analytics = await db_client.get_order_analytics(
                customer_id=customer_id,
                days=analysis_period_days,
                auth_token=auth_token
            )
            
            # Get time-based patterns
            time_patterns = await db_client.get_orders_by_period(
                customer_id=customer_id,
                days=analysis_period_days,
                group_by=group_by,
                auth_token=auth_token
            )
            
            # Analyze patterns
            trends = _analyze_customer_trends(time_patterns.get("periods", []))
            
            result = {
                "success": True,
                "customer_id": customer_id,
                "customer_analytics": customer_analytics,
                "time_patterns": time_patterns,
                "trends": trends,
                "analysis_summary": {
                    "period_days": analysis_period_days,
                    "grouping": group_by,
                    "has_activity": customer_analytics.get("total_orders", 0) > 0
                },
                "request_info": {
                    "tool": "analyze_customer_spending_patterns",
                    "analysis_date": datetime.utcnow().isoformat(),
                    "data_source": "payment_service_orders"
                }
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to analyze customer patterns: {str(e)}")
    
    @mcp_server.tool
    async def get_top_customers_analysis(
        analysis_period_days: int = 30,
        top_count: int = 10,
        sort_by: Literal["volume", "amount", "frequency"] = "amount",
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analysis of top customers by various metrics.
        
        This tool identifies and analyzes the most valuable customers based on
        order volume, transaction amounts, or transaction frequency.
        
        Args:
            analysis_period_days: Number of days to analyze
            top_count: Number of top customers to return
            sort_by: How to rank customers (volume, amount, frequency)
        
        Returns:
            dict: Top customers analysis including:
                - top_customers: List of top customers with their metrics
                - customer_insights: Analysis of customer behavior
                - business_metrics: Overall business insights
                - period_summary: Summary for the analysis period
        
        Raises:
            SasaiAPIError: If analysis fails
        """
        try:
            # Ensure database connection
            await db_client.connect()
            
            # Get top customers data
            top_customers_data = await db_client.get_top_customers(
                days=analysis_period_days,
                limit=top_count,
                auth_token=auth_token
            )
            
            # Get overall analytics for comparison
            overall_analytics = await db_client.get_order_analytics(
                days=analysis_period_days
            )
            
            # Analyze customer insights
            customer_insights = _analyze_top_customers(
                top_customers_data.get("top_customers", []),
                overall_analytics
            )
            
            result = {
                "success": True,
                "top_customers": top_customers_data,
                "overall_analytics": overall_analytics,
                "customer_insights": customer_insights,
                "analysis_parameters": {
                    "period_days": analysis_period_days,
                    "top_count": top_count,
                    "sort_by": sort_by
                },
                "request_info": {
                    "tool": "get_top_customers_analysis",
                    "analysis_date": datetime.utcnow().isoformat(),
                    "data_source": "payment_service_orders"
                }
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to get top customers analysis: {str(e)}")
    
    @mcp_server.tool
    async def search_orders_advanced(
        search_criteria: Dict[str, Any],
        max_results: int = 100,
        search_days_back: int = 90,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Advanced search through order data with multiple filter criteria.
        
        This tool allows complex filtering and searching of order records to find
        specific transactions or analyze particular order patterns.
        
        Args:
            search_criteria: Dictionary with search filters including:
                - customer_id: Filter by customer
                - amount_min/amount_max: Filter by amount range
                - order_type: Filter by order type
                - currency: Filter by currency
                - status: Filter by order status
            max_results: Maximum number of orders to return
            search_days_back: How many days back to search
        
        Returns:
            dict: Advanced search results including:
                - matching_orders: List of orders matching criteria
                - search_summary: Summary statistics of matches
                - filters_applied: The criteria that were applied
                - insights: Analysis of search results
        
        Raises:
            SasaiAPIError: If search fails or invalid criteria provided
        """
        try:
            # Ensure database connection
            await db_client.connect()
            
            # Execute search
            search_results = await db_client.search_orders(
                search_criteria=search_criteria,
                limit=max_results,
                days_back=search_days_back,
                auth_token=auth_token
            )
            
            # Analyze search results
            search_insights = _analyze_search_results(
                search_results.get("matching_orders", []),
                search_criteria
            )
            
            result = {
                "success": True,
                "search_results": search_results,
                "search_insights": search_insights,
                "search_parameters": {
                    "criteria": search_criteria,
                    "max_results": max_results,
                    "search_days_back": search_days_back
                },
                "request_info": {
                    "tool": "search_orders_advanced",
                    "search_date": datetime.utcnow().isoformat(),
                    "data_source": "payment_service_orders"
                }
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to search orders: {str(e)}")


def _analyze_customer_trends(periods: List[Dict]) -> Dict[str, Any]:
    """Analyze customer spending trends from time-based data"""
    
    if not periods or len(periods) < 2:
        return {
            "trend": "insufficient_data",
            "message": "Not enough data points to identify trends"
        }
    
    # Calculate trend in order amounts
    amounts = [period.get("total_amount", 0) for period in periods]
    
    if len(amounts) >= 3:
        # Simple trend analysis
        recent_avg = sum(amounts[-3:]) / 3
        earlier_avg = sum(amounts[:-3]) / max(1, len(amounts) - 3)
        
        if recent_avg > earlier_avg * 1.1:
            trend = "increasing"
        elif recent_avg < earlier_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return {
        "spending_trend": trend,
        "total_periods": len(periods),
        "average_orders_per_period": sum(p.get("order_count", 0) for p in periods) / len(periods),
        "peak_period": max(periods, key=lambda x: x.get("total_amount", 0)) if periods else None
    }


def _analyze_top_customers(customers: List[Dict], overall_stats: Dict) -> Dict[str, Any]:
    """Analyze insights from top customers data"""
    
    if not customers:
        return {"message": "No customer data available"}
    
    total_customers_amount = sum(c.get("total_amount", 0) for c in customers)
    overall_amount = overall_stats.get("total_amount", 0)
    
    top_customer_percentage = (total_customers_amount / overall_amount * 100) if overall_amount > 0 else 0
    
    # Find most common order types among top customers
    all_order_types = []
    for customer in customers:
        all_order_types.extend(customer.get("order_types", []))
    
    order_type_counts = {}
    for order_type in all_order_types:
        order_type_counts[order_type] = order_type_counts.get(order_type, 0) + 1
    
    return {
        "top_customers_revenue_percentage": round(top_customer_percentage, 2),
        "average_order_value_top_customers": total_customers_amount / sum(c.get("total_orders", 0) for c in customers) if customers else 0,
        "most_popular_order_types": sorted(order_type_counts.items(), key=lambda x: x[1], reverse=True)[:3],
        "customer_concentration": "high" if top_customer_percentage > 80 else "medium" if top_customer_percentage > 60 else "low"
    }


def _analyze_search_results(orders: List[Dict], criteria: Dict) -> Dict[str, Any]:
    """Analyze and provide insights from search results"""
    
    if not orders:
        return {
            "message": "No orders found matching the search criteria",
            "suggestions": "Try broadening your search criteria or extending the time period"
        }
    
    # Basic statistics
    amounts = [order.get("payerAmount", 0) for order in orders]
    fees = [order.get("feeAmount", 0) for order in orders]
    
    # Time distribution
    dates = []
    for order in orders:
        if "createdDate" in order:
            dates.append(order["createdDate"])
    
    return {
        "result_summary": {
            "total_matches": len(orders),
            "total_amount": sum(amounts),
            "total_fees": sum(fees),
            "average_amount": sum(amounts) / len(amounts) if amounts else 0,
            "date_range": {
                "earliest": min(dates).strftime("%Y-%m-%d") if dates else None,
                "latest": max(dates).strftime("%Y-%m-%d") if dates else None
            }
        },
        "search_effectiveness": "good" if len(orders) > 10 else "limited" if len(orders) > 0 else "no_results"
    }
