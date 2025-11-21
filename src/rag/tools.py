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
    
    # RAG API endpoint - Direct retrieval API (no double LLM calls)
    RAG_API_BASE_URL = "http://localhost:8000/api/retriever"
    
    # Default tenant configuration for Sasai (matching your existing setup)
    DEFAULT_TENANT_ID = "sasai"
    DEFAULT_TENANT_SUB_ID = "sasai-sub"
    DEFAULT_KNOWLEDGE_BASE_ID = "sasai-compliance-kb"
    
    # Default provider config ID for embeddings (from your curl example)
    DEFAULT_PROVIDER_CONFIG_ID = "azure-openai-llm-gpt-4o-mini"
    
    # Default retrieval parameters
    DEFAULT_LIMIT = 5
    DEFAULT_MIN_SCORE = 0.1
    DEFAULT_RERANK = False
    
    # Request timeout settings
    REQUEST_TIMEOUT = 30.0


async def call_rag_retrieval_service(
    query: str,
    knowledge_base_id: str = RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID,
    tenant_id: str = RAGConfig.DEFAULT_TENANT_ID,
    tenant_sub_id: str = RAGConfig.DEFAULT_TENANT_SUB_ID,
    provider_config_id: str = RAGConfig.DEFAULT_PROVIDER_CONFIG_ID,
    limit: int = RAGConfig.DEFAULT_LIMIT,
    min_score: float = RAGConfig.DEFAULT_MIN_SCORE
) -> Dict[str, Any]:
    """
    Call the RAG retrieval service directly to get document chunks.
    
    This function calls the raw retrieval API without additional LLM processing,
    allowing Claude to be the single point of intelligence for synthesis.
    
    Args:
        query: The search query
        knowledge_base_id: Knowledge base to search
        tenant_id: Tenant context
        tenant_sub_id: Tenant sub-context
        provider_config_id: Provider config for embeddings
        limit: Maximum number of results
        min_score: Minimum similarity score
    
    Returns:
        dict: Retrieval service response with document chunks
    
    Raises:
        SasaiAPIError: If retrieval service call fails
    """
    try:
        # Build the retrieval API URL
        retrieval_url = f"{RAGConfig.RAG_API_BASE_URL}/{knowledge_base_id}"
        
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
        
        # Make HTTP GET request to retrieval service (matching the curl format)
        async with httpx.AsyncClient(timeout=RAGConfig.REQUEST_TIMEOUT) as client:
            response = await client.get(
                retrieval_url,
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                error_text = response.text if hasattr(response, 'text') else str(response.content)
                raise SasaiAPIError(
                    f"RAG Retrieval API error ({response.status_code}): {error_text}"
                )
            
            data = response.json()
            
            # Process the retrieval results
            if "results" in data and isinstance(data["results"], list):
                # Format the retrieved chunks for Claude to process
                formatted_chunks = []
                for result in data["results"]:
                    chunk_info = {
                        "text": result.get("text", ""),
                        "score": result.get("score", 0.0),
                        "metadata": result.get("metadata", {}),
                        "chunk_id": result.get("chunk_id", "")
                    }
                    formatted_chunks.append(chunk_info)
                
                return {
                    "success": True,
                    "source": "rag_retrieval",
                    "knowledge_base": knowledge_base_id,
                    "query": query,
                    "retrieved_chunks": formatted_chunks,
                    "total_chunks": len(formatted_chunks),
                    "retrieval_parameters": {
                        "limit": limit,
                        "min_score": min_score,
                        "provider_config_id": provider_config_id
                    }
                }
            else:
                raise SasaiAPIError("RAG retrieval service returned unexpected response format")
                
    except httpx.TimeoutException:
        raise SasaiAPIError("RAG retrieval service request timed out. Please try again.")
    except httpx.RequestError as e:
        raise SasaiAPIError(f"Failed to connect to RAG retrieval service: {str(e)}")
    except Exception as e:
        raise SasaiAPIError(f"Unexpected error calling RAG retrieval service: {str(e)}")


def register_rag_tools(mcp_server) -> None:
    """
    Register RAG (compliance knowledge) tools with the MCP server.
    
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
        try:
            # Enhance question with knowledge area context
            enhanced_query = question
            if knowledge_area and knowledge_area != "general":
                enhanced_query = f"{knowledge_area} {question}"
            
            # Call retrieval service directly (no LLM processing)
            result = await call_rag_retrieval_service(
                query=enhanced_query,
                knowledge_base_id=RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID,
                tenant_id=RAGConfig.DEFAULT_TENANT_ID,
                tenant_sub_id=RAGConfig.DEFAULT_TENANT_SUB_ID
            )
            
            # Enhance response with metadata
            result["request_info"] = {
                "original_question": question,
                "knowledge_area": knowledge_area,
                "user_context": user_context,
                "tool": "wallet_query_compliance_knowledge",
                "note": "Raw document chunks retrieved for Claude to synthesize"
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to query compliance knowledge: {str(e)}")
    
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
        try:
            # Create wallet-specific query
            wallet_query = f"wallet {topic}"
            if policy_type:
                wallet_query = f"wallet {policy_type} {topic}"
            
            # Add compliance context
            enhanced_query = f"{wallet_query} policy procedures requirements"
            
            # Call retrieval service directly
            result = await call_rag_retrieval_service(
                query=enhanced_query,
                knowledge_base_id=RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID,
                tenant_id=RAGConfig.DEFAULT_TENANT_ID,
                tenant_sub_id=RAGConfig.DEFAULT_TENANT_SUB_ID
            )
            
            # Add wallet-specific metadata
            result["request_info"] = {
                "topic": topic,
                "policy_type": policy_type,
                "search_scope": "wallet_compliance",
                "tool": "wallet_search_compliance_policies",
                "note": "Raw policy document chunks retrieved for Claude to analyze"
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to search wallet compliance policies: {str(e)}")
    
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
        try:
            # Build regulatory query
            reg_query = f"{regulation} regulation {jurisdiction}"
            if wallet_specific:
                reg_query = f"wallet payment {reg_query} compliance requirements"
            
            # Add regulatory context
            enhanced_query = f"{reg_query} guidance requirements documentation"
            
            # Call retrieval service directly
            result = await call_rag_retrieval_service(
                query=enhanced_query,
                knowledge_base_id=RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID,
                tenant_id=RAGConfig.DEFAULT_TENANT_ID,
                tenant_sub_id=RAGConfig.DEFAULT_TENANT_SUB_ID
            )
            
            # Add regulatory metadata
            result["request_info"] = {
                "regulation": regulation,
                "jurisdiction": jurisdiction,
                "wallet_specific": wallet_specific,
                "tool": "wallet_get_regulatory_guidance",
                "note": "Raw regulatory document chunks retrieved for Claude to synthesize"
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to get regulatory guidance: {str(e)}")
