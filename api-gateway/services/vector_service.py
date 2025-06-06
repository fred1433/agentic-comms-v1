import asyncio
import time
import hashlib
from typing import List, Dict, Optional, Tuple
import structlog
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncAzureOpenAI

from config import settings

logger = structlog.get_logger()

class VectorService:
    """Service for vector embeddings and contextual memory using Pinecone"""
    
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = 1536  # OpenAI text-embedding-ada-002 dimension
        
        # Initialize OpenAI for embeddings
        self.openai_client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        self.index = None
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure Pinecone index exists"""
        try:
            # Check if index exists
            if self.index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                
                # Create index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                
                # Wait for index to be ready
                import time
                time.sleep(10)
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error("Failed to initialize Pinecone index", error=str(e))
            raise
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error("Failed to create embedding", error=str(e))
            raise
    
    async def store_conversation_context(
        self,
        conversation_id: str,
        message: str,
        response: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store conversation context in vector database"""
        try:
            # Create combined text for embedding
            combined_text = f"User: {message}\nAssistant: {response}"
            
            # Generate embedding
            embedding = await self.create_embedding(combined_text)
            
            # Create unique ID
            text_hash = hashlib.md5(combined_text.encode()).hexdigest()
            vector_id = f"{conversation_id}_{text_hash}_{int(time.time())}"
            
            # Prepare metadata
            vector_metadata = {
                "conversation_id": conversation_id,
                "user_message": message,
                "assistant_response": response,
                "timestamp": time.time(),
                "text_length": len(combined_text),
                **(metadata or {})
            }
            
            # Store in Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding, vector_metadata)]
            )
            
            logger.info(
                "Stored conversation context",
                conversation_id=conversation_id,
                vector_id=vector_id,
                text_length=len(combined_text)
            )
            
            return vector_id
            
        except Exception as e:
            logger.error("Failed to store conversation context", error=str(e))
            raise
    
    async def retrieve_relevant_context(
        self,
        conversation_id: str,
        query: str,
        top_k: int = 5,
        include_global: bool = True
    ) -> List[Dict]:
        """Retrieve relevant conversation context"""
        try:
            # Create embedding for query
            query_embedding = await self.create_embedding(query)
            
            # Build filter for conversation-specific context
            filter_dict = {"conversation_id": conversation_id}
            
            # Search conversation-specific context
            conversation_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            
            # Process conversation-specific results
            for match in conversation_results.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "conversation_id": match.metadata.get("conversation_id"),
                    "user_message": match.metadata.get("user_message"),
                    "assistant_response": match.metadata.get("assistant_response"),
                    "timestamp": match.metadata.get("timestamp"),
                    "source": "conversation"
                })
            
            # If enabled, also search global context (from other conversations)
            if include_global and len(results) < top_k:
                remaining_slots = top_k - len(results)
                
                global_results = self.index.query(
                    vector=query_embedding,
                    top_k=remaining_slots * 2,  # Get more to filter out current conversation
                    include_metadata=True
                )
                
                # Filter out current conversation and add global context
                for match in global_results.matches:
                    if (match.metadata.get("conversation_id") != conversation_id and 
                        len(results) < top_k):
                        results.append({
                            "id": match.id,
                            "score": match.score,
                            "conversation_id": match.metadata.get("conversation_id"),
                            "user_message": match.metadata.get("user_message"),
                            "assistant_response": match.metadata.get("assistant_response"),
                            "timestamp": match.metadata.get("timestamp"),
                            "source": "global"
                        })
            
            # Sort by relevance score
            results.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(
                "Retrieved relevant context",
                conversation_id=conversation_id,
                query_length=len(query),
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Failed to retrieve context", error=str(e))
            return []
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """Get summary of conversation from stored context"""
        try:
            # Retrieve all context for this conversation
            all_context = self.index.query(
                vector=[0.0] * self.dimension,  # Dummy vector
                top_k=100,
                include_metadata=True,
                filter={"conversation_id": conversation_id}
            )
            
            if not all_context.matches:
                return None
            
            # Sort by timestamp
            sorted_context = sorted(
                all_context.matches,
                key=lambda x: x.metadata.get("timestamp", 0)
            )
            
            # Build conversation text
            conversation_text = []
            for match in sorted_context:
                user_msg = match.metadata.get("user_message", "")
                assistant_msg = match.metadata.get("assistant_response", "")
                conversation_text.append(f"User: {user_msg}")
                conversation_text.append(f"Assistant: {assistant_msg}")
            
            return "\n".join(conversation_text)
            
        except Exception as e:
            logger.error("Failed to get conversation summary", error=str(e))
            return None
    
    async def delete_conversation_context(self, conversation_id: str) -> bool:
        """Delete all context for a conversation"""
        try:
            # Get all vectors for this conversation
            results = self.index.query(
                vector=[0.0] * self.dimension,
                top_k=1000,
                include_metadata=True,
                filter={"conversation_id": conversation_id}
            )
            
            if results.matches:
                # Delete all vectors
                vector_ids = [match.id for match in results.matches]
                self.index.delete(ids=vector_ids)
                
                logger.info(
                    "Deleted conversation context",
                    conversation_id=conversation_id,
                    vectors_deleted=len(vector_ids)
                )
            
            return True
            
        except Exception as e:
            logger.error("Failed to delete conversation context", error=str(e))
            return False
    
    async def store_knowledge_base(self, documents: List[Dict]) -> List[str]:
        """Store knowledge base documents for global context"""
        try:
            vectors_to_upsert = []
            vector_ids = []
            
            for doc in documents:
                # Create embedding for document
                embedding = await self.create_embedding(doc["content"])
                
                # Generate unique ID
                doc_hash = hashlib.md5(doc["content"].encode()).hexdigest()
                vector_id = f"kb_{doc.get('category', 'general')}_{doc_hash}"
                
                # Prepare metadata
                metadata = {
                    "type": "knowledge_base",
                    "category": doc.get("category", "general"),
                    "title": doc.get("title", ""),
                    "content": doc["content"],
                    "source": doc.get("source", ""),
                    "timestamp": time.time(),
                    **doc.get("metadata", {})
                }
                
                vectors_to_upsert.append((vector_id, embedding, metadata))
                vector_ids.append(vector_id)
            
            # Batch upsert
            self.index.upsert(vectors=vectors_to_upsert)
            
            logger.info(
                "Stored knowledge base documents",
                document_count=len(documents),
                vector_ids_count=len(vector_ids)
            )
            
            return vector_ids
            
        except Exception as e:
            logger.error("Failed to store knowledge base", error=str(e))
            return []
    
    async def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Search knowledge base for relevant information"""
        try:
            # Create query embedding
            query_embedding = await self.create_embedding(query)
            
            # Build filter
            filter_dict = {"type": "knowledge_base"}
            if category:
                filter_dict["category"] = category
            
            # Search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    "id": match.id,
                    "score": match.score,
                    "title": match.metadata.get("title"),
                    "content": match.metadata.get("content"),
                    "category": match.metadata.get("category"),
                    "source": match.metadata.get("source")
                })
            
            logger.info(
                "Searched knowledge base",
                query_length=len(query),
                category=category,
                results_count=len(formatted_results)
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error("Knowledge base search failed", error=str(e))
            return []
    
    async def get_index_stats(self) -> Dict:
        """Get statistics about the vector index"""
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
            
        except Exception as e:
            logger.error("Failed to get index stats", error=str(e))
            return {}
    
    async def health_check(self) -> bool:
        """Check if vector service is healthy"""
        try:
            # Test embedding creation
            test_embedding = await self.create_embedding("Health check test")
            
            # Test index connectivity
            stats = await self.get_index_stats()
            
            return bool(test_embedding and stats)
            
        except Exception as e:
            logger.error("Vector service health check failed", error=str(e))
            return False 