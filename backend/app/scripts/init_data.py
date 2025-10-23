#!/usr/bin/env python3
"""
Initialize demo data for Agentic AI system
Loads sample incidents and knowledge base into vector store
"""

import json
import asyncio
import logging
from typing import List, Dict, Any
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataInitializer:
    """Initialize demo data in vector store and database"""
    
    def __init__(self):
        self.chroma_host = os.environ.get('CHROMA_HOST', 'http://localhost:8000')
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.data_path = Path('/app/data/sample_data.json')
        
    async def initialize(self):
        """Main initialization method"""
        logger.info("Starting data initialization...")
        
        try:
            # Load sample data
            data = self.load_sample_data()
            
            # Initialize ChromaDB
            client = self.init_chromadb()
            
            # Create collections
            incidents_collection = self.create_collection(client, "incidents")
            knowledge_collection = self.create_collection(client, "knowledge")
            
            # Load incidents
            await self.load_incidents(incidents_collection, data['incidents'])
            
            # Load knowledge base
            await self.load_knowledge(knowledge_collection, data['knowledge_base'])
            
            logger.info("✅ Data initialization completed successfully!")
            
            # Print statistics
            self.print_statistics(incidents_collection, knowledge_collection)
            
        except Exception as e:
            logger.error(f"Failed to initialize data: {e}")
            raise
    
    def load_sample_data(self) -> Dict[str, Any]:
        """Load sample data from JSON file"""
        if not self.data_path.exists():
            # Try alternate path
            self.data_path = Path('/app/sample_data.json')
            
        if not self.data_path.exists():
            # Create minimal sample data if file doesn't exist
            logger.warning("Sample data file not found, creating minimal dataset...")
            return self.create_minimal_dataset()
        
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data.get('incidents', []))} incidents and {len(data.get('knowledge_base', []))} knowledge articles")
        return data
    
    def create_minimal_dataset(self) -> Dict[str, Any]:
        """Create minimal dataset for demo if file is missing"""
        return {
            "incidents": [
                {
                    "id": "INC001",
                    "title": "Database connection timeout",
                    "description": "Users experiencing timeout errors when accessing the application",
                    "category": "Database",
                    "priority": "High",
                    "error_message": "Connection timeout after 30 seconds",
                    "affected_systems": ["Database", "Application"],
                    "resolution": "Increase connection pool size and optimize queries",
                    "resolution_time": 45,
                    "team": "Database Team"
                },
                {
                    "id": "INC002",
                    "title": "API Gateway 502 errors",
                    "description": "API Gateway returning Bad Gateway errors intermittently",
                    "category": "Network",
                    "priority": "Critical",
                    "error_message": "502 Bad Gateway",
                    "affected_systems": ["API Gateway", "Backend Services"],
                    "resolution": "Restart services and clear cache",
                    "resolution_time": 30,
                    "team": "Platform Team"
                },
                {
                    "id": "INC003",
                    "title": "Memory leak in service",
                    "description": "Service consuming excessive memory over time",
                    "category": "Application",
                    "priority": "High",
                    "error_message": "OutOfMemoryError",
                    "affected_systems": ["Application Service"],
                    "resolution": "Fix memory leak and deploy patch",
                    "resolution_time": 120,
                    "team": "Development Team"
                }
            ],
            "knowledge_base": [
                {
                    "id": "KB001",
                    "title": "Database Connection Best Practices",
                    "category": "Database",
                    "content": "Configure connection pools with appropriate size, timeout values, and validation queries",
                    "tags": ["database", "connection", "performance"]
                },
                {
                    "id": "KB002",
                    "title": "API Gateway Troubleshooting",
                    "category": "Network",
                    "content": "Check upstream services, verify routing, clear cache, review rate limits",
                    "tags": ["api", "gateway", "troubleshooting"]
                },
                {
                    "id": "KB003",
                    "title": "Memory Management Guide",
                    "category": "Application",
                    "content": "Monitor heap usage, analyze dumps, identify leaks, implement proper cleanup",
                    "tags": ["memory", "performance", "debugging"]
                }
            ],
            "feedback_data": []
        }
    
    def init_chromadb(self) -> chromadb.Client:
        """Initialize ChromaDB client"""
        # Parse host URL
        if self.chroma_host.startswith('http://'):
            host = self.chroma_host.replace('http://', '').split(':')[0]
            port = int(self.chroma_host.split(':')[-1]) if ':' in self.chroma_host else 8000
        else:
            host = 'localhost'
            port = 8000
        
        logger.info(f"Connecting to ChromaDB at {host}:{port}")
        
        # Try HTTP client first (for containerized setup)
        try:
            client = chromadb.HttpClient(host=host, port=port)
            # Test connection
            client.heartbeat()
            logger.info("Connected to ChromaDB via HTTP")
            return client
        except:
            # Fallback to persistent client for local development
            logger.info("HTTP connection failed, using persistent client")
            client = chromadb.PersistentClient(path="./chroma_db")
            return client
    
    def create_collection(self, client: chromadb.Client, name: str) -> chromadb.Collection:
        """Create or get a ChromaDB collection"""
        try:
            # Try to get existing collection
            collection = client.get_collection(name=name)
            logger.info(f"Using existing collection: {name}")
            # Clear existing data for fresh start
            collection.delete(where={})
            logger.info(f"Cleared existing data in collection: {name}")
        except:
            # Create new collection
            collection = client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {name}")
        
        return collection
    
    async def load_incidents(self, collection: chromadb.Collection, incidents: List[Dict[str, Any]]):
        """Load incidents into vector store"""
        logger.info(f"Loading {len(incidents)} incidents...")
        
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for incident in incidents:
            # Create searchable document
            doc_text = f"""
            Title: {incident['title']}
            Description: {incident['description']}
            Category: {incident['category']}
            Priority: {incident['priority']}
            Error: {incident.get('error_message', '')}
            Systems: {', '.join(incident.get('affected_systems', []))}
            Resolution: {incident.get('resolution', '')}
            Root Cause: {incident.get('root_cause', '')}
            Prevention: {incident.get('prevention', '')}
            """
            
            documents.append(doc_text)
            metadatas.append({
                "id": incident['id'],
                "title": incident['title'],
                "category": incident['category'],
                "priority": incident['priority'],
                "resolution_time": str(incident.get('resolution_time', 0)),
                "team": incident.get('team', 'Support')
            })
            ids.append(incident['id'])
            
            # Generate embedding
            embedding = self.embedding_model.encode(doc_text)
            embeddings.append(embedding.tolist())
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        
        logger.info(f"✓ Loaded {len(incidents)} incidents into vector store")
    
    async def load_knowledge(self, collection: chromadb.Collection, knowledge_articles: List[Dict[str, Any]]):
        """Load knowledge base articles into vector store"""
        logger.info(f"Loading {len(knowledge_articles)} knowledge articles...")
        
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for article in knowledge_articles:
            # Create searchable document
            doc_text = f"""
            Title: {article['title']}
            Category: {article['category']}
            Content: {article['content']}
            Tags: {', '.join(article.get('tags', []))}
            """
            
            documents.append(doc_text)
            metadatas.append({
                "id": article['id'],
                "title": article['title'],
                "category": article['category'],
                "tags": ','.join(article.get('tags', []))
            })
            ids.append(article['id'])
            
            # Generate embedding
            embedding = self.embedding_model.encode(doc_text)
            embeddings.append(embedding.tolist())
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        
        logger.info(f"✓ Loaded {len(knowledge_articles)} knowledge articles into vector store")
    
    def print_statistics(self, incidents_collection, knowledge_collection):
        """Print statistics about loaded data"""
        try:
            incidents_count = incidents_collection.count()
            knowledge_count = knowledge_collection.count()
            
            print("\n" + "="*50)
            print("📊 Data Initialization Complete!")
            print("="*50)
            print(f"✅ Incidents loaded: {incidents_count}")
            print(f"✅ Knowledge articles loaded: {knowledge_count}")
            print(f"✅ Vector dimensions: 384")
            print(f"✅ Embedding model: all-MiniLM-L6-v2")
            print("="*50)
            print("🚀 System ready for demo!")
            print("="*50 + "\n")
        except Exception as e:
            logger.warning(f"Could not print statistics: {e}")

async def main():
    """Main entry point"""
    initializer = DataInitializer()
    await initializer.initialize()

if __name__ == "__main__":
    # Wait for services to be ready
    import time
    logger.info("Waiting for services to be ready...")
    time.sleep(10)  # Give ChromaDB time to start
    
    # Run initialization
    asyncio.run(main())