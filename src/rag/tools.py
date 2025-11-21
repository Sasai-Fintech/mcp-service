"""
RAG (Retrieval Augmented Generation) tools for FastMCP server.
Integrates with Sasai compliance knowledge base and AI agent.
"""

import httpx
import asyncio
import json
from typing import Dict, Any, Optional, Literal

from config.settings import SasaiConfig
from core.exceptions import SasaiAPIError


class RAGConfig:
    """Configuration for RAG service integration"""
    
    # Default retrieval parameters (not duplicated from SasaiConfig)
    DEFAULT_LIMIT = 5
    DEFAULT_MIN_SCORE = 0.1
    DEFAULT_RERANK = False


async def call_rag_retrieval_service(
    query: str,
    knowledge_base_id: str = None,
    tenant_id: str = None,
    tenant_sub_id: str = None,
    provider_config_id: str = None,
    limit: int = RAGConfig.DEFAULT_LIMIT,
    min_score: float = RAGConfig.DEFAULT_MIN_SCORE
) -> Dict[str, Any]:
    """
    Call the RAG retrieval service directly to get document chunks.
    
    This function calls the raw retrieval API without additional LLM processing,
    allowing Claude to be the single point of intelligence for synthesis.
    
    Args:
        query: The search query
        knowledge_base_id: Knowledge base to search (defaults to SasaiConfig.RAG_KNOWLEDGE_BASE_ID)
        tenant_id: Tenant context (defaults to SasaiConfig.RAG_TENANT_ID)
        tenant_sub_id: Tenant sub-context (defaults to SasaiConfig.RAG_TENANT_SUB_ID)
        provider_config_id: Provider config for embeddings (defaults to SasaiConfig.RAG_PROVIDER_CONFIG_ID)
        limit: Maximum number of results
        min_score: Minimum similarity score
    
    Returns:
        dict: Retrieval service response with document chunks
    
    Raises:
        SasaiAPIError: If retrieval service call fails
    """
    try:
        # Use SasaiConfig defaults if not provided
        knowledge_base_id = knowledge_base_id or SasaiConfig.RAG_KNOWLEDGE_BASE_ID
        tenant_id = tenant_id or SasaiConfig.RAG_TENANT_ID
        tenant_sub_id = tenant_sub_id or SasaiConfig.RAG_TENANT_SUB_ID
        provider_config_id = provider_config_id or SasaiConfig.RAG_PROVIDER_CONFIG_ID
        
        # Build the retrieval API URL using SasaiConfig
        retrieval_url = f"{SasaiConfig.RAG_SERVICE_URL}/{knowledge_base_id}"
        
        # Prepare request headers (matching the curl example)
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-ID": tenant_id,
            "X-Tenant-Sub-ID": tenant_sub_id
        }
        
        # Prepare request parameters
        params = {
            "query": query,
            "provider_config_id": provider_config_id,
            "limit": limit,
            "min_score": min_score
        }
        
        # Make HTTP GET request using SasaiConfig.RAG_REQUEST_TIMEOUT
        async with httpx.AsyncClient(timeout=SasaiConfig.RAG_REQUEST_TIMEOUT) as client:
            response = await client.get(
                retrieval_url,
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                error_text = response.text if hasattr(response, 'text') else str(response.content)
                raise SasaiAPIError(
                    f"RAG retrieval service call failed with status {response.status_code}: {error_text}",
                    status_code=response.status_code,
                    endpoint=retrieval_url
                )
            
            # Return the raw response from retrieval service
            response_data = response.json()
            
            # Add metadata about the query for context
            response_data["query_metadata"] = {
                "original_query": query,
                "knowledge_base_id": knowledge_base_id,
                "tenant_id": tenant_id,
                "tenant_sub_id": tenant_sub_id,
                "provider_config_id": provider_config_id,
                "limit": limit,
                "min_score": min_score,
                "retrieval_url": retrieval_url
            }
            
            return response_data
            
    except httpx.HTTPError as e:
        raise SasaiAPIError(f"HTTP error during RAG retrieval: {str(e)}")
    except json.JSONDecodeError as e:
        raise SasaiAPIError(f"Invalid JSON response from RAG service: {str(e)}")
    except Exception as e:
        if isinstance(e, SasaiAPIError):
            raise
        raise SasaiAPIError(f"Unexpected error during RAG retrieval: {str(e)}")


def register_rag_tools(mcp_server) -> None:
    """
    Register RAG (Retrieval Augmented Generation) tools with the MCP server.
    
    Args:
        mcp_server: FastMCP server instance
    """
    
    @mcp_server.tool
    async def wallet_query_compliance_knowledge(
        question: str,
        knowledge_area: Optional[Literal["general", "financial", "legal", "regulatory", "policy"]] = "general",
        user_context: str = "wallet_user"
    ) -> Dict[str, Any]:
        """
        Query the Sasai compliance knowledge base for answers to compliance-related questions.
        
        This tool retrieves relevant document chunks from the compliance knowledge base,
        returning raw content for Claude to synthesize into a comprehensive answer.
        
        Args:
            question: The compliance question or query to search for
            knowledge_area: Specific area of compliance knowledge to focus on
            user_context: Context about the user making the request
        
        Returns:
            dict: Retrieved document chunks including:
                - retrieved_chunks: List of relevant document chunks with text and metadata
                - total_chunks: Number of chunks retrieved
                - query: Original search query
                - knowledge_base: Source knowledge base used
        
        Raises:
            SasaiAPIError: If the knowledge base query fails or returns an error
        """
        # Enhance the query with knowledge area context
        enhanced_query = f"{knowledge_area} compliance: {question}" if knowledge_area != "general" else question
        
        try:
            # Call the RAG retrieval service using SasaiConfig defaults
            result = await call_rag_retrieval_service(
                query=enhanced_query,
                limit=10,  # Get more results for comprehensive compliance guidance
                min_score=0.1
            )
            
            # Extract and format the response for the wallet context
            chunks = result.get("chunks", [])
            
            return {
                "retrieved_chunks": chunks,
                "total_chunks": len(chunks),
                "query": enhanced_query,
                "knowledge_base": result.get("query_metadata", {}).get("knowledge_base_id", "unknown"),
                "knowledge_area": knowledge_area,
                "user_context": user_context
            }
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Compliance knowledge query failed: {str(e)}")
    
    @mcp_server.tool
    async def wallet_search_compliance_policies(
        topic: str,
        policy_type: Optional[Literal["aml", "kyc", "fraud", "transaction_limits", "privacy"]] = None
    ) -> Dict[str, Any]:
        """
        Search for wallet-specific compliance policies and procedures.
        
        This tool searches the compliance knowledge base for policies specifically 
        related to wallet operations, retrieving raw document chunks for Claude to analyze.
        
        Args:
            topic: The compliance topic or policy area to search for
            policy_type: Specific type of wallet compliance policy
        
        Returns:
            dict: Wallet compliance policy document chunks including:
                - retrieved_chunks: List of relevant policy document chunks
                - total_chunks: Number of chunks retrieved
                - query: Search query used
                - compliance_context: Policy context and metadata
        
        Raises:
            SasaiAPIError: If the policy search fails or returns no results
        """
        # Build policy-focused search query
        search_terms = ["wallet", "policy", topic]
        if policy_type:
            search_terms.append(policy_type)
        
        policy_query = f"wallet policy {topic}" + (f" {policy_type}" if policy_type else "")
        
        try:
            # Search for policy documents using SasaiConfig defaults
            result = await call_rag_retrieval_service(
                query=policy_query,
                limit=8,  # Focus on most relevant policy documents
                min_score=0.15  # Higher threshold for policy precision
            )
            
            chunks = result.get("chunks", [])
            
            return {
                "retrieved_chunks": chunks,
                "total_chunks": len(chunks),
                "query": policy_query,
                "compliance_context": {
                    "topic": topic,
                    "policy_type": policy_type,
                    "search_focus": "wallet_compliance_policies"
                }
            }
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Compliance policy search failed: {str(e)}")
    
    @mcp_server.tool
    async def wallet_get_regulatory_guidance(
        regulation: str,
        jurisdiction: Optional[Literal["us", "eu", "uk", "zw", "international"]] = "international",
        wallet_specific: bool = True
    ) -> Dict[str, Any]:
        """
        Get regulatory guidance for wallet operations and financial services.
        
        This tool retrieves regulatory information and guidance documents 
        relevant to wallet operations and payment processing from the compliance knowledge base.
        
        Args:
            regulation: The specific regulation or regulatory topic
            jurisdiction: The legal jurisdiction for the regulation
            wallet_specific: Whether to focus on wallet-specific regulatory guidance
        
        Returns:
            dict: Retrieved regulatory guidance chunks including:
                - retrieved_chunks: List of relevant regulatory document chunks
                - total_chunks: Number of chunks retrieved
                - regulatory_context: Regulation and jurisdiction metadata
                - query: Search query used
        
        Raises:
            SasaiAPIError: If regulatory guidance retrieval fails
        """
        # Build regulation-focused query
        regulation_terms = [regulation, jurisdiction, "regulation"]
        if wallet_specific:
            regulation_terms.extend(["wallet", "payment", "financial services"])
        
        reg_query = f"{regulation} regulation {jurisdiction}" + (" wallet payment" if wallet_specific else "")
        
        try:
            # Search regulatory guidance using SasaiConfig defaults
            result = await call_rag_retrieval_service(
                query=reg_query,
                limit=6,  # Focus on most relevant regulatory guidance
                min_score=0.2  # Higher threshold for regulatory precision
            )
            
            chunks = result.get("chunks", [])
            
            return {
                "retrieved_chunks": chunks,
                "total_chunks": len(chunks),
                "regulatory_context": {
                    "regulation": regulation,
                    "jurisdiction": jurisdiction,
                    "wallet_specific": wallet_specific
                },
                "query": reg_query
            }
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Regulatory guidance retrieval failed: {str(e)}")
