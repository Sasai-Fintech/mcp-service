"""
Database module for MongoDB access and Orders analytics.
"""

from .tools import register_database_tools
from .client import DatabaseClient, DatabaseConfig

__all__ = [
    "register_database_tools",
    "DatabaseClient", 
    "DatabaseConfig"
]
