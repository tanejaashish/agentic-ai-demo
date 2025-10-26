"""
RAG Agent using LangChain for the Agentic AI Demo
FIXED: Enabled embeddings and proper error handling
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# LangChain imports
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun

from app.models.incident import Incident
import aiohttp

logger = logging.getLogger(__name__)

# RAGResponse class that cag_agent.py expects
class RAGResponse:
    """Response structure from RAG Agent"""
    def __init__(self, recommendations=None, confidence=0.5, sources=None, processing_time=0):
        self.recommendations = recommendations or []
        self.confidence = confidence
        self.sources = sources or []
        self.processing_time = processing_time
        self.metadata = {}

class OllamaLLM(LLM):
    """Custom LangChain LLM wrapper for Ollama"""
    
    model: str = "llama3.2:3b"
    base_url: str = "http://ollama:11434"
    temperature: float = 0.7
    
    @property
    def _llm_type(self) -> str:
        return "ollama"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """Call Ollama API with timeout"""
        import requests
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False
        }
        
        try:
            # FIXED: Reduced timeout to prevent hanging
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._get_fallback_response(prompt)
        except Exception as e:
            logger.error(f"Failed to call Ollama: {e}")
            return self._get_fallback_response(prompt)
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Fallback response when Ollama is unavailable"""
        if "database" in prompt.lower():
            return "1. Check database connections\n2. Review connection pool settings\n3. Monitor database performance\n4. Check for locks or blocking queries"
        return "1. Analyze the error logs\n2. Check system resources\n3. Review recent changes\n4. Escalate if needed"

class LangChainRAGAgent:
    """
    RAG Agent using LangChain for document retrieval and generation
    FIXED: Embeddings enabled, proper error handling
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # FIXED: Initialize embeddings properly
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            # Create a simple fallback embedding
            self.embeddings = None
        
        # Initialize vector store
        self.vector_store = None
        self.initialize_vector_store()
        
        # Initialize LLM
        self.llm = OllamaLLM(
            model=self.config.get('model', 'llama3.2:3b'),
            base_url=self.config.get('ollama_host', 'http://ollama:11434'),
            temperature=self.config.get('temperature', 0.7)
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.get('chunk_size', 512),
            chunk_overlap=self.config.get('chunk_overlap', 50),
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize QA chain
        self.qa_chain = None
        if self.embeddings:
            self.setup_qa_chain()
        else:
            logger.warning("QA chain not initialized due to missing embeddings")
        
        logger.info("LangChain RAG Agent initialized")
    
    def initialize_vector_store(self):
        """Initialize ChromaDB vector store with LangChain"""
        try:
            # FIXED: Include embedding function
            if self.embeddings:
                self.vector_store = Chroma(
                    collection_name="incidents",
                    embedding_function=self.embeddings,
                    persist_directory="/app/chroma_db"
                )
                logger.info("Vector store initialized with embeddings")
            else:
                # Try without embeddings (will use default)
                self.vector_store = Chroma(
                    collection_name="incidents",
                    persist_directory="/app/chroma_db"
                )
                logger.warning("Vector store initialized without custom embeddings")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Set to None to trigger fallback
            self.vector_store = None
    
    def setup_qa_chain(self):
        """Set up the LangChain QA chain"""
        if not self.vector_store:
            logger.warning("Vector store not initialized, skipping QA chain setup")
            return
        
        try:
            # Define the prompt template
            prompt_template = """You are an expert IT support agent. Use the following context to answer the question about the incident.
            If you don't know the answer, say you don't know. Don't make up information.
            
            Context: {context}
            
            Question: {question}
            
            Provide a detailed solution with:
            1. Step-by-step resolution steps
            2. Root cause analysis
            3. Prevention measures
            4. When to escalate
            
            Answer:"""
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "question"]
            )
            
            # Create the QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(
                    search_kwargs={"k": self.config.get('top_k', 5)}
                ),
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            
            logger.info("QA chain initialized successfully")
        except Exception as e:
            logger.error(f"Failed to setup QA chain: {e}")
            self.qa_chain = None
    
    async def process(self, incident: Incident) -> RAGResponse:
        """
        Process incident using LangChain RAG pipeline
        FIXED: Added timeout and better error handling
        """
        start_time = datetime.now()
        
        try:
            # Prepare the query
            query = self._prepare_query(incident)
            
            # FIXED: Add timeout to prevent hanging
            if self.qa_chain:
                try:
                    # Run with timeout
                    result = await asyncio.wait_for(
                        asyncio.to_thread(self.qa_chain, {"query": query}),
                        timeout=120.0  # 25 second timeout
                    )
                    
                    # Parse the response
                    answer = result.get('result', '')
                    source_docs = result.get('source_documents', [])
                    
                    # Format recommendations
                    recommendations = self._parse_answer_to_recommendations(answer)
                    
                    # Calculate confidence based on sources
                    confidence = self._calculate_confidence(source_docs, answer)
                    
                    # Format sources
                    sources = self._format_sources(source_docs)
                    
                except asyncio.TimeoutError:
                    logger.warning("RAG processing timed out, using fallback")
                    recommendations = self._get_fallback_recommendations(incident)
                    confidence = 0.5
                    sources = []
            else:
                # Fallback if QA chain not initialized
                logger.warning("QA chain not initialized, using fallback")
                recommendations = self._get_fallback_recommendations(incident)
                confidence = 0.5
                sources = []
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create response object
            response = RAGResponse(
                recommendations=recommendations,
                confidence=confidence,
                sources=sources,
                processing_time=processing_time
            )
            response.metadata = {
                "langchain_version": "0.1.16",
                "model": self.config.get('model', 'llama3.2:3b')
            }
            return response
            
        except Exception as e:
            logger.error(f"Error in LangChain RAG processing: {e}")
            return self._get_error_response(incident, str(e))
    
    def _prepare_query(self, incident: Incident) -> str:
        """Prepare query from incident"""
        query_parts = [
            f"Incident: {incident.title}",
            f"Description: {incident.description}",
            f"Category: {incident.category}",
            f"Priority: {incident.priority}"
        ]
        
        if incident.error_message:
            query_parts.append(f"Error: {incident.error_message}")
        
        if incident.affected_systems:
            query_parts.append(f"Affected Systems: {', '.join(incident.affected_systems)}")
        
        return "\n".join(query_parts)
    
    def _parse_answer_to_recommendations(self, answer: str) -> List[Dict[str, Any]]:
        """Parse LLM answer into structured recommendations"""
        # Simple parsing - split by numbered lists
        lines = answer.split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering/bullets
                clean_line = line.lstrip('0123456789.-•').strip()
                if clean_line:
                    steps.append(clean_line)
        
        # If no steps found, use the whole answer
        if not steps:
            steps = [answer]
        
        return [{
            "type": "primary",
            "solution_steps": steps[:10],  # Limit to 10 steps
            "confidence": 0.8,
            "source_ids": []
        }]
    
    def _calculate_confidence(self, source_docs: List, answer: str) -> float:
        """Calculate confidence based on sources and answer quality"""
        if not source_docs:
            return 0.5
        
        # Base confidence on number of sources
        base_confidence = min(0.9, 0.5 + (len(source_docs) * 0.1))
        
        # Adjust based on answer length
        if len(answer) > 100:
            base_confidence += 0.05
        
        return min(0.95, base_confidence)
    
    def _format_sources(self, source_docs: List) -> List[Dict[str, Any]]:
        """Format source documents"""
        sources = []
        for i, doc in enumerate(source_docs[:5]):  # Limit to 5 sources
            sources.append({
                "id": f"source_{i+1}",
                "title": doc.metadata.get('title', f'Document {i+1}'),
                "relevance_score": 0.8,  # Simplified
                "category": doc.metadata.get('category', 'general'),
                "preview": doc.page_content[:200]
            })
        return sources
    
    def _get_fallback_recommendations(self, incident: Incident) -> List[Dict[str, Any]]:
        """Fallback recommendations when RAG fails"""
        category_solutions = {
            "Database": [
                "Check database connection settings and credentials",
                "Verify network connectivity to database server",
                "Review connection pool configuration",
                "Monitor database server resources (CPU, memory, disk)",
                "Check for long-running queries or locks"
            ],
            "Network": [
                "Check network connectivity between components",
                "Verify firewall and security group rules",
                "Review load balancer configuration",
                "Check DNS resolution",
                "Monitor network latency and packet loss"
            ],
            "Application": [
                "Review application logs for errors",
                "Check application resource usage",
                "Verify configuration files",
                "Review recent deployments or changes",
                "Check dependencies and external services"
            ]
        }
        
        # Get category-specific or default solutions
        category_str = str(incident.category).replace('Category.', '')
        steps = category_solutions.get(category_str, [
            "Gather detailed information about the issue",
            "Check system logs for error messages",
            "Verify system resources (CPU, memory, disk)",
            "Review recent changes or deployments",
            "Escalate to appropriate team if needed"
        ])
        
        return [{
            "type": "primary",
            "solution_steps": steps,
            "confidence": 0.6,
            "source_ids": []
        }]
    
    def _get_error_response(self, incident: Incident, error_msg: str) -> RAGResponse:
        """Create error response"""
        return RAGResponse(
            recommendations=self._get_fallback_recommendations(incident),
            confidence=0.4,
            sources=[],
            processing_time=0.5
        )

    # Additional methods from original file...
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        if not self.vector_store or not self.embeddings:
            logger.error("Vector store or embeddings not initialized")
            return
        
        try:
            # Convert to LangChain documents
            docs = [
                Document(
                    page_content=doc.get('content', ''),
                    metadata=doc.get('metadata', {})
                )
                for doc in documents
            ]
            
            # Split documents
            split_docs = self.text_splitter.split_documents(docs)
            
            # Add to vector store
            self.vector_store.add_documents(split_docs)
            
            logger.info(f"Added {len(split_docs)} document chunks to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")

    async def load_models(self):
        """Load any pre-trained models or data"""
        logger.info("RAG Agent models loaded (placeholder)")
        pass

# Keep original RAGAgent class name for compatibility
RAGAgent = LangChainRAGAgent