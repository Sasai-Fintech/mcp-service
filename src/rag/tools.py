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
    
    # RAG API endpoint - Your existing cortex RAG service
    RAG_API_URL = "http://localhost:8000/teams/agent"
    
    # Default tenant configuration for Sasai (matching your existing setup)
    DEFAULT_TENANT_ID = "sasai"
    DEFAULT_TENANT_SUB_ID = "sasai-sub"
    DEFAULT_KNOWLEDGE_BASE_ID = "sasai-compliance-kb"
    
    # Request timeout settings
    REQUEST_TIMEOUT = 3000.0


async def call_rag_service(
    query: str,
    user_id: str = "mcp_user",
    tenant_id: str = RAGConfig.DEFAULT_TENANT_ID,
    knowledge_base_id: str = RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID
) -> Dict[str, Any]:
    """
    Call the RAG service with a compliance query.
    
    Args:
        query: The compliance question or query
        user_id: User identifier for the request
        tenant_id: Tenant context (default: sasai)
        knowledge_base_id: Knowledge base to search
    
    Returns:
        dict: RAG service response with answer and metadata
    
    Raises:
        SasaiAPIError: If RAG service call fails
    """
    try:
        # Prepare request payload (matching your Teams bot format)
        request_payload = {
            "text": query,
            "message": query,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "tenant_sub_id": RAGConfig.DEFAULT_TENANT_SUB_ID,
            "knowledge_base_id": knowledge_base_id,
            "source": "fastmcp_wallet_server",
            "context": "wallet_operations"
        }
        
        # Make HTTP request to RAG service
        async with httpx.AsyncClient(timeout=RAGConfig.REQUEST_TIMEOUT) as client:
            response = await client.post(
                RAGConfig.RAG_API_URL,
                headers={"Content-Type": "application/json"},
                json=request_payload
            )
            
            if response.status_code != 200:
                error_text = response.text if hasattr(response, 'text') else str(response.content)
                raise SasaiAPIError(
                    f"RAG API error ({response.status_code}): {error_text}"
                )
            
            data = response.json()
            
            # Extract response based on your API format
            if data and data.get("text"):
                return {
                    "success": True,
                    "answer": data["text"],
                    "source": "rag_service",
                    "knowledge_base": knowledge_base_id,
                    "query": query,
                    "raw_response": data
                }
            elif data and data.get("response"):
                return {
                    "success": True,
                    "answer": data["response"],
                    "source": "rag_service",
                    "knowledge_base": knowledge_base_id,
                    "query": query,
                    "raw_response": data
                }
            else:
                raise SasaiAPIError("RAG service returned unexpected response format")
                
    except httpx.TimeoutException:
        raise SasaiAPIError("RAG service request timed out. Please try again.")
    except httpx.RequestError as e:
        raise SasaiAPIError(f"Failed to connect to RAG service: {str(e)}")
    except Exception as e:
        raise SasaiAPIError(f"Unexpected error calling RAG service: {str(e)}")


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
        
        This tool provides access to the company's compliance documentation, policies, and 
        regulatory information through an AI-powered knowledge base search.
        
        Args:
            question: The compliance question or query to search for
            knowledge_area: Specific area of compliance knowledge to focus on
            user_context: Context about the user making the request
        
        Returns:
            dict: Compliance knowledge response including:
                - answer: AI-generated answer based on knowledge base
                - knowledge_base: Source knowledge base used
                - confidence: Confidence level of the answer
                - sources: Referenced documents or policies
        
        Raises:
            SasaiAPIError: If the knowledge base query fails or returns an error
        """
        try:
            # Enhance question with knowledge area context
            enhanced_query = question
            if knowledge_area and knowledge_area != "general":
                enhanced_query = f"[{knowledge_area.upper()}] {question}"
            
            # Call RAG service
            result = await call_rag_service(
                query=enhanced_query,
                user_id=user_context,
                tenant_id=RAGConfig.DEFAULT_TENANT_ID,
                knowledge_base_id=RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID
            )
            
            # Enhance response with metadata
            result["request_info"] = {
                "original_question": question,
                "knowledge_area": knowledge_area,
                "user_context": user_context,
                "tool": "wallet_query_compliance_knowledge"
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
        related to wallet operations, payment processing, and financial compliance.
        
        Args:
            topic: The compliance topic or policy area to search for
            policy_type: Specific type of wallet compliance policy
        
        Returns:
            dict: Wallet compliance policy information including:
                - policy_details: Relevant policy information
                - compliance_requirements: Specific requirements for wallet operations
                - procedures: Step-by-step compliance procedures
                - contact_info: Compliance team contact information
        
        Raises:
            SasaiAPIError: If the policy search fails or returns no results
        """
        try:
            # Create wallet-specific query
            wallet_query = f"wallet {topic}"
            if policy_type:
                wallet_query = f"wallet {policy_type} {topic}"
            
            # Add compliance context
            enhanced_query = f"[WALLET_COMPLIANCE] {wallet_query} policy procedures requirements"
            
            # Call RAG service
            result = await call_rag_service(
                query=enhanced_query,
                user_id="wallet_compliance_user",
                tenant_id=RAGConfig.DEFAULT_TENANT_ID,
                knowledge_base_id=RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID
            )
            
            # Add wallet-specific metadata
            result["request_info"] = {
                "topic": topic,
                "policy_type": policy_type,
                "search_scope": "wallet_compliance",
                "tool": "wallet_search_compliance_policies"
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
        relevant to wallet operations and payment processing.
        
        Args:
            regulation: The specific regulation or regulatory topic
            jurisdiction: The legal jurisdiction for the regulation
            wallet_specific: Whether to focus on wallet-specific regulatory guidance
        
        Returns:
            dict: Regulatory guidance including:
                - guidance_summary: Summary of regulatory requirements
                - compliance_steps: Required compliance actions
                - deadlines: Important compliance deadlines
                - documentation: Required documentation and records
        
        Raises:
            SasaiAPIError: If regulatory guidance retrieval fails
        """
        try:
            # Build regulatory query
            reg_query = f"{regulation} regulation {jurisdiction}"
            if wallet_specific:
                reg_query = f"wallet payment {reg_query} compliance requirements"
            
            # Add regulatory context
            enhanced_query = f"[REGULATORY] {reg_query} guidance requirements documentation"
            
            # Call RAG service
            result = await call_rag_service(
                query=enhanced_query,
                user_id="regulatory_compliance_user",
                tenant_id=RAGConfig.DEFAULT_TENANT_ID,
                knowledge_base_id=RAGConfig.DEFAULT_KNOWLEDGE_BASE_ID
            )
            
            # Add regulatory metadata
            result["request_info"] = {
                "regulation": regulation,
                "jurisdiction": jurisdiction,
                "wallet_specific": wallet_specific,
                "tool": "wallet_get_regulatory_guidance"
            }
            
            return result
            
        except Exception as e:
            if isinstance(e, SasaiAPIError):
                raise
            raise SasaiAPIError(f"Failed to get regulatory guidance: {str(e)}")
