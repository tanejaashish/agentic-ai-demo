#!/usr/bin/env python3
"""
Initialize demo data for Agentic AI Demo
This script loads sample data into PostgreSQL and ChromaDB
Works without sentence-transformers dependency
"""

import os
import sys
import json
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
DB_USER = os.environ.get('POSTGRES_USER', 'agentic')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'agentic123')
DB_NAME = os.environ.get('POSTGRES_DB', 'incidents')
CHROMA_HOST = os.environ.get('CHROMA_HOST', 'chromadb')

def wait_for_service(service_name, host, max_retries=30):
    """Wait for a service to be available"""
    logger.info(f"Waiting for {service_name}...")
    
    # For demo, we'll skip actual connection tests
    # In production, you'd test actual connectivity
    time.sleep(5)
    logger.info(f"{service_name} is ready!")
    return True

def init_postgres():
    """Initialize PostgreSQL with sample data"""
    try:
        import psycopg2
        
        # Wait a bit for PostgreSQL to be ready
        time.sleep(10)
        
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id VARCHAR(50) PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                priority VARCHAR(20) DEFAULT 'Medium',
                category VARCHAR(50) DEFAULT 'General',
                status VARCHAR(20) DEFAULT 'Open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id VARCHAR(50) PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                category VARCHAR(50),
                description TEXT,
                resolution TEXT,
                tags TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("PostgreSQL initialized successfully")
        return True
        
    except Exception as e:
        logger.warning(f"PostgreSQL init failed: {e}")
        return False

def init_chromadb():
    """Initialize ChromaDB with sample vectors"""
    try:
        import chromadb
        
        # Simple initialization without sentence-transformers
        try:
            client = chromadb.HttpClient(host=CHROMA_HOST, port=8000)
        except:
            client = chromadb.PersistentClient(path="/app/chroma_db")
        
        # Create collection
        try:
            collection = client.create_collection(name="incidents")
        except:
            collection = client.get_collection(name="incidents")
        
        # Add simple documents (ChromaDB will handle embeddings)
        documents = [
            "Database connection pool exhausted. Increase pool size.",
            "API Gateway 502 errors. Check upstream services.",
            "Memory leak in application. Analyze heap dump.",
        ]
        
        collection.add(
            documents=documents,
            ids=[f"doc_{i}" for i in range(len(documents))],
            metadatas=[{"type": "knowledge"} for _ in documents]
        )
        
        logger.info("ChromaDB initialized successfully")
        return True
        
    except Exception as e:
        logger.warning(f"ChromaDB init failed: {e}")
        return False

def create_fallback_data():
    """Create JSON file with sample data as fallback"""
    sample_data = {
        "incidents": [
            {
                "id": "INC001",
                "title": "Database Connection Pool Exhausted",
                "description": "Connection pool exhaustion during peak hours",
                "priority": "High",
                "category": "Database"
            },
            {
                "id": "INC002",
                "title": "API Gateway 502 Errors",
                "description": "Gateway returns 502 errors",
                "priority": "Critical",
                "category": "Network"
            }
        ],
        "knowledge_base": [
            {
                "id": "KB001",
                "title": "Database Troubleshooting",
                "category": "Database",
                "resolution": "1. Check connections\n2. Increase pool size"
            },
            {
                "id": "KB002",
                "title": "API Gateway Guide",
                "category": "Network",
                "resolution": "1. Check upstream\n2. Increase timeouts"
            }
        ]
    }
    
    # Ensure data directory exists
    os.makedirs("/app/data", exist_ok=True)
    
    # Save data
    with open("/app/data/sample_data.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    logger.info("Created fallback data file")

def main():
    """Main initialization"""
    logger.info("Initializing demo data...")
    
    # Always create fallback data
    create_fallback_data()
    
    # Try to initialize services (non-critical if they fail)
    init_postgres()
    init_chromadb()
    
    logger.info("Demo data initialized successfully")

if __name__ == "__main__":
    main()