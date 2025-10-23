"""
Vector Store Service for ChromaDB integration
Handles document storage, retrieval, and similarity search
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from datetime import datetime
import chromadb
from chromadb.config import Settings
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    # Fallback if sentence_transformers has issues
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
            print(f"Using mock SentenceTransformer for {model_name}")
        
        def encode(self, texts):
            # Return mock embeddings
            import numpy as np
            if isinstance(texts, str):
                texts = [texts]
            return np.random.randn(len(texts), 384)
import hashlib

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Service for managing vector storage and retrieval using ChromaDB
    """
    
    def __init__(self, host: str = "localhost:8000", collection_name: str = "incidents"):
        self.host = host
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        #self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_model = None  # Let ChromaDB use its default embeddings
        self.initialized = False
        
        logger.info(f"VectorStoreService initialized with host: {host}")
    
    async def initialize(self):
        """Initialize connection to ChromaDB"""
        try:
            # Parse host
            if self.host.startswith('http://'):
                host_parts = self.host.replace('http://', '').split(':')
                host = host_parts[0]
                port = int(host_parts[1]) if len(host_parts) > 1 else 8000
            else:
                host = self.host.split(':')[0]
                port = int(self.host.split(':')[1]) if ':' in self.host else 8000
            
            # Try HTTP client first (for Docker setup)
            try:
                self.client = chromadb.HttpClient(host=host, port=port)
                self.client.heartbeat()
                logger.info("Connected to ChromaDB via HTTP")
            except:
                # Fallback to persistent client for local development
                self.client = chromadb.PersistentClient(path="./chroma_db")
                logger.info("Using persistent ChromaDB client")
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            self.initialized = True
            logger.info("VectorStoreService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorStoreService: {e}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search for the query
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            documents = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    score = 1 - results['distances'][0][i]  # Convert distance to similarity
                    
                    if score >= threshold:
                        documents.append({
                            'id': results['ids'][0][i] if 'ids' in results else f"doc_{i}",
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                            'score': score,
                            'title': results['metadatas'][0][i].get('title', 'Untitled') if results['metadatas'] else 'Untitled',
                            'category': results['metadatas'][0][i].get('category', 'general') if results['metadatas'] else 'general'
                        })
            
            logger.info(f"Found {len(documents)} documents for query")
            return documents
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search (simplified for demo)
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # For demo purposes, we'll use the similarity search
            # In production, this would be a proper keyword search
            return await self.similarity_search(query, k)
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    async def add_document(
        self,
        id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Add a document to the vector store
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Add to collection
            self.collection.add(
                ids=[id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Document {id} added to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
    
    async def update_document(
        self,
        id: str,
        content: str,
        metadata: Dict[str, Any]
    ):
        """
        Update an existing document
        """
        try:
            # Delete old version
            self.collection.delete(ids=[id])
            
            # Add new version
            await self.add_document(id, content, metadata)
            
            logger.info(f"Document {id} updated")
            
        except Exception as e:
            logger.error(f"Failed to update document: {e}")
            raise
    
    async def delete_document(self, id: str):
        """
        Delete a document from the vector store
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            self.collection.delete(ids=[id])
            logger.info(f"Document {id} deleted")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            count = self.collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": "all-MiniLM-L6-v2",
                "vector_dimensions": 384,
                "initialized": self.initialized
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def close(self):
        """
        Close the vector store connection
        """
        if self.client:
            # ChromaDB doesn't require explicit closing
            self.initialized = False
            logger.info("VectorStoreService closed")