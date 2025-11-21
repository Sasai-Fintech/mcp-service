"""
MongoDB client for Orders data access and analytics.
"""

import os
import jwt
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

from core.exceptions import SasaiAPIError


# Country to currency mapping for auto-detection
COUNTRY_CURRENCY_MAP = {
    "ZW": "ZWL",  # Zimbabwe - Zimbabwe Dollar
    "US": "USD",  # United States - US Dollar  
    "ZA": "ZAR",  # South Africa - South African Rand
    "BW": "BWP",  # Botswana - Botswana Pula
    "MW": "MWK",  # Malawi - Malawian Kwacha
    "ZM": "ZMW",  # Zambia - Zambian Kwacha
    "MZ": "MZN",  # Mozambique - Mozambican Metical
    # Add more country-currency mappings as needed
}


class DatabaseConfig:
    """Configuration for MongoDB database access"""
    
    # MongoDB connection string
    MONGODB_URI = "mongodb+srv://sasairagengine:j3ugUjql4I60TY52@sandbox.detzo.mongodb.net/?retryWrites=true&w=majority&appName=sandbox"
    
    # Database and collection names - Based on our exploration
    PAYMENT_DATABASE = "payment-service-sandbox"
    ORDERS_COLLECTION = "Orders"
    PAYMENTS_COLLECTION = "Payments"
    
    USER_DATABASE = "user-service-sandbox" 
    CUSTOMERS_COLLECTION = "Customers"
    
    # Connection settings
    CONNECTION_TIMEOUT = 10000  # 10 seconds
    SERVER_SELECTION_TIMEOUT = 5000  # 5 seconds


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token to extract customer information.
    
    Args:
        token: JWT token string (with or without 'Bearer ' prefix)
        
    Returns:
        Dict containing decoded token data with customer_id and countryCode
        
    Raises:
        SasaiAPIError: If token decoding fails
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Decode without verification (since we just need to extract data)
        # In production, you might want to verify the signature
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        return {
            "customer_id": decoded.get("customerId") or decoded.get("customer_id") or decoded.get("sub"),
            "country_code": decoded.get("countryCode") or decoded.get("country_code"),
            "user_id": decoded.get("userId") or decoded.get("user_id"),
            "full_token_data": decoded
        }
        
    except jwt.InvalidTokenError as e:
        raise SasaiAPIError(f"Invalid JWT token: {str(e)}")
    except Exception as e:
        raise SasaiAPIError(f"Failed to decode JWT token: {str(e)}")


def get_customer_context(auth_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract customer context from authentication token.
    
    Args:
        auth_token: Optional JWT token to extract customer info from
        
    Returns:
        Dict with customer context or empty dict if no token
    """
    if not auth_token:
        return {}
    
    try:
        return decode_jwt_token(auth_token)
    except SasaiAPIError:
        # If token decoding fails, return empty context
        # This allows the system to continue without authentication
        return {}


class DatabaseClient:
    """MongoDB client for Orders data access and analytics"""
    
    def __init__(self):
        """Initialize the database client"""
        self.client = None
        self.payment_db = None
        self.user_db = None
        
    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(
                DatabaseConfig.MONGODB_URI,
                serverSelectionTimeoutMS=DatabaseConfig.SERVER_SELECTION_TIMEOUT,
                connectTimeoutMS=DatabaseConfig.CONNECTION_TIMEOUT
            )
            
            # Test connection
            await self.client.server_info()
            
            # Get databases
            self.payment_db = self.client[DatabaseConfig.PAYMENT_DATABASE]
            self.user_db = self.client[DatabaseConfig.USER_DATABASE]
            
        except ServerSelectionTimeoutError:
            raise SasaiAPIError("Failed to connect to MongoDB: Connection timeout")
        except Exception as e:
            raise SasaiAPIError(f"Failed to connect to MongoDB: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
    
    async def get_order_analytics(
        self, 
        customer_id: Optional[str] = None,
        days: int = 30,
        order_type: Optional[str] = None,
        currency: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get order analytics from the Orders collection.
        
        Args:
            customer_id: Optional customer filter
            days: Number of days to look back
            order_type: Optional filter by order type
            currency: Optional filter by currency
            auth_token: JWT token to extract customer context
        
        Returns:
            Dictionary with order analytics
        """
        if self.payment_db is None:
            await self.connect()
        
        # Extract customer context from token if provided
        customer_context = get_customer_context(auth_token)
        
        # Use customer_id from token if not explicitly provided
        if not customer_id and customer_context.get("customer_id"):
            customer_id = customer_context["customer_id"]
        
        # Use country-specific currency if available
        if not currency and customer_context.get("country_code"):
            country_to_currency = {
                "ZW": "ZWG", "ZA": "ZAR", "NG": "NGN", "GH": "GHS", 
                "KE": "KES", "UG": "UGX", "US": "USD", "GB": "GBP"
            }
            currency = country_to_currency.get(customer_context["country_code"])
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build query
            query = {
                "createdDate": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            if customer_id:
                query["payerInfo.customerId"] = customer_id
            if order_type:
                query["type"] = order_type
            if currency:
                query["currency"] = currency
            
            # Aggregation pipeline for analytics
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "total_orders": {"$sum": 1},
                        "total_amount": {"$sum": "$payerAmount"},
                        "total_fees": {"$sum": "$feeAmount"},
                        "average_amount": {"$avg": "$payerAmount"},
                        "max_amount": {"$max": "$payerAmount"},
                        "min_amount": {"$min": "$payerAmount"},
                        "order_types": {"$addToSet": "$type"},
                        "currencies": {"$addToSet": "$currency"},
                        "statuses": {"$addToSet": "$status"}
                    }
                }
            ]
            
            # Execute aggregation
            result = await self.payment_db[DatabaseConfig.ORDERS_COLLECTION].aggregate(
                pipeline
            ).to_list(length=1)
            
            if not result:
                return {
                    "total_orders": 0,
                    "total_amount": 0.0,
                    "total_fees": 0.0,
                    "average_amount": 0.0,
                    "max_amount": 0.0,
                    "min_amount": 0.0,
                    "order_types": [],
                    "currencies": [],
                    "statuses": []
                }
            
            analytics = result[0]
            analytics.pop("_id", None)  # Remove the _id field
            
            # Add customer context to results
            if customer_context:
                analytics["customer_context"] = {
                    "customer_id": customer_context.get("customer_id"),
                    "country_code": customer_context.get("country_code"),
                    "filters_applied": {
                        "customer_specific": bool(customer_id),
                        "currency_from_country": bool(currency and customer_context.get("country_code"))
                    }
                }
            
            return analytics
            
        except OperationFailure as e:
            raise SasaiAPIError(f"Orders analytics query failed: {str(e)}")
        except Exception as e:
            raise SasaiAPIError(f"Unexpected analytics error: {str(e)}")
    
    async def get_orders_by_period(
        self,
        customer_id: Optional[str] = None,
        days: int = 30,
        group_by: str = "day",  # day, week, month
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get orders grouped by time period.
        
        Args:
            customer_id: Optional customer filter
            days: Number of days to analyze
            group_by: How to group the data (day, week, month)
            auth_token: JWT token to extract customer context
        
        Returns:
            Dictionary with time-based order analysis
        """
        if self.payment_db is None:
            await self.connect()
        
        # Extract customer context from token if provided
        customer_context = get_customer_context(auth_token)
        
        # Use customer_id from token if not explicitly provided
        if not customer_id and customer_context.get("customer_id"):
            customer_id = customer_context["customer_id"]
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build base query
            query = {
                "createdDate": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            if customer_id:
                query["payerInfo.customerId"] = customer_id
            
            # Date grouping based on period
            if group_by == "day":
                date_group = {
                    "year": {"$year": "$createdDate"},
                    "month": {"$month": "$createdDate"},
                    "day": {"$dayOfMonth": "$createdDate"}
                }
            elif group_by == "week":
                date_group = {
                    "year": {"$year": "$createdDate"},
                    "week": {"$week": "$createdDate"}
                }
            else:  # month
                date_group = {
                    "year": {"$year": "$createdDate"},
                    "month": {"$month": "$createdDate"}
                }
            
            # Aggregation pipeline
            pipeline = [
                {"$match": query},
                {
                    "$group": {
                        "_id": date_group,
                        "order_count": {"$sum": 1},
                        "total_amount": {"$sum": "$payerAmount"},
                        "total_fees": {"$sum": "$feeAmount"},
                        "average_amount": {"$avg": "$payerAmount"}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            # Execute aggregation
            periods = await self.payment_db[DatabaseConfig.ORDERS_COLLECTION].aggregate(
                pipeline
            ).to_list(length=100)
            
            return {
                "periods": periods,
                "group_by": group_by,
                "analysis_days": days,
                "total_periods": len(periods)
            }
            
        except OperationFailure as e:
            raise SasaiAPIError(f"Period analysis failed: {str(e)}")
        except Exception as e:
            raise SasaiAPIError(f"Unexpected period analysis error: {str(e)}")
    
    async def get_top_customers(
        self,
        days: int = 30,
        limit: int = 10,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get top customers by order volume and amount.
        
        Args:
            days: Number of days to analyze
            limit: Number of top customers to return
            auth_token: JWT token to extract customer context (for country-specific filtering)
        
        Returns:
            Dictionary with top customer analysis
        """
        if self.payment_db is None:
            await self.connect()
        
        # Extract customer context from token if provided
        customer_context = get_customer_context(auth_token)
        
        # Auto-detect currency based on country if authenticated
        detected_currency = None
        if customer_context.get("country_code"):
            detected_currency = COUNTRY_CURRENCY_MAP.get(customer_context["country_code"])
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build match criteria
            match_criteria = {
                "createdDate": {
                    "$gte": start_date,
                    "$lte": end_date
                },
                "payerInfo.customerId": {"$exists": True, "$ne": None}
            }
            
            # Add currency filter if detected from country context
            if detected_currency:
                match_criteria["currency"] = detected_currency
            
            # Aggregation pipeline for top customers
            pipeline = [
                {"$match": match_criteria},
                {
                    "$group": {
                        "_id": "$payerInfo.customerId",
                        "total_orders": {"$sum": 1},
                        "total_amount": {"$sum": "$payerAmount"},
                        "total_fees": {"$sum": "$feeAmount"},
                        "average_order_amount": {"$avg": "$payerAmount"},
                        "order_types": {"$addToSet": "$type"},
                        "currencies": {"$addToSet": "$currency"}
                    }
                },
                {"$sort": {"total_amount": -1}},
                {"$limit": limit}
            ]
            
            # Execute aggregation
            customers = await self.payment_db[DatabaseConfig.ORDERS_COLLECTION].aggregate(
                pipeline
            ).to_list(length=limit)
            
            return {
                "top_customers": customers,
                "analysis_period_days": days,
                "customer_count": len(customers),
                "customer_context": customer_context,
                "currency_filter": detected_currency
            }
            
        except OperationFailure as e:
            raise SasaiAPIError(f"Top customers analysis failed: {str(e)}")
        except Exception as e:
            raise SasaiAPIError(f"Unexpected top customers error: {str(e)}")
    
    async def search_orders(
        self,
        search_criteria: Dict[str, Any],
        limit: int = 100,
        days_back: int = 90,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search orders based on specific criteria.
        
        Args:
            search_criteria: Dictionary with search filters
            limit: Maximum number of orders to return
            days_back: How many days back to search
            auth_token: JWT token to extract customer context
        
        Returns:
            Dictionary with search results
        """
        if self.payment_db is None:
            await self.connect()
        
        # Extract customer context from token if provided
        customer_context = get_customer_context(auth_token)
        
        # Auto-detect currency based on country if authenticated
        detected_currency = None
        if customer_context.get("country_code"):
            detected_currency = COUNTRY_CURRENCY_MAP.get(customer_context["country_code"])
        
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Build search query
            query = {
                "createdDate": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            # Add customer context if authenticated and no explicit customer_id provided
            if customer_context.get("customer_id") and "customer_id" not in search_criteria:
                query["payerInfo.customerId"] = customer_context["customer_id"]
            
            # Add search criteria
            if "customer_id" in search_criteria:
                query["payerInfo.customerId"] = search_criteria["customer_id"]
            
            if "amount_min" in search_criteria:
                query.setdefault("payerAmount", {})["$gte"] = search_criteria["amount_min"]
            
            if "amount_max" in search_criteria:
                query.setdefault("payerAmount", {})["$lte"] = search_criteria["amount_max"]
            
            if "order_type" in search_criteria:
                query["type"] = search_criteria["order_type"]
            
            # Use detected currency if no explicit currency provided
            if "currency" in search_criteria:
                query["currency"] = search_criteria["currency"]
            elif detected_currency:
                query["currency"] = detected_currency
                query["currency"] = search_criteria["currency"]
            
            if "status" in search_criteria:
                query["status"] = search_criteria["status"]
            
            # Execute search
            orders = await self.payment_db[DatabaseConfig.ORDERS_COLLECTION].find(
                query
            ).limit(limit).to_list(length=limit)
            
            # Calculate summary
            total_amount = sum(order.get("payerAmount", 0) for order in orders)
            total_fees = sum(order.get("feeAmount", 0) for order in orders)
            
            return {
                "matching_orders": orders,
                "search_criteria": search_criteria,
                "total_matches": len(orders),
                "summary": {
                    "total_amount": total_amount,
                    "total_fees": total_fees,
                    "average_amount": total_amount / len(orders) if orders else 0
                },
                "search_period_days": days_back,
                "customer_context": customer_context,
                "currency_filter": detected_currency,
                "query_applied": query
            }
            
        except OperationFailure as e:
            raise SasaiAPIError(f"Orders search failed: {str(e)}")
        except Exception as e:
            raise SasaiAPIError(f"Unexpected search error: {str(e)}")


# Global database client instance
db_client = DatabaseClient()
