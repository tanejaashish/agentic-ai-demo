"""
RAG Agent using LangChain for the Agentic AI Demo
This version properly integrates with LangChain
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
        """Call Ollama API"""
        import requests
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
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
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize embeddings
        #self.embeddings = HuggingFaceEmbeddings(
            #model_name="sentence-transformers/all-MiniLM-L6-v2",
            #model_kwargs={'device': 'cpu'},
            #encode_kwargs={'normalize_embeddings': True}
        #)
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
        self.setup_qa_chain()
        
        logger.info("LangChain RAG Agent initialized")
    
    def initialize_vector_store(self):
        """Initialize ChromaDB vector store with LangChain"""
        try:
            self.vector_store = Chroma(
                collection_name="incidents",
                #embedding_function=self.embeddings,
                persist_directory="/app/chroma_db"
            )
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Create in-memory vector store as fallback
            self.vector_store = Chroma(
                collection_name="incidents",
                embedding_function=self.embeddings
            )
    
    def setup_qa_chain(self):
        """Set up the LangChain QA chain"""
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return
        
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
        
        logger.info("QA chain initialized")
    
    async def process(self, incident: Incident) -> RAGResponse: #-> Dict[str, Any]:
        """
        Process incident using LangChain RAG pipeline
        """
        start_time = datetime.now()
        
        try:
            # Prepare the query
            query = self._prepare_query(incident)
            
            # Run the QA chain
            if self.qa_chain:
                result = await asyncio.to_thread(self.qa_chain, {"query": query})
                
                # Parse the response
                answer = result.get('result', '')
                source_docs = result.get('source_documents', [])
                
                # Format recommendations
                recommendations = self._parse_answer_to_recommendations(answer)
                
                # Calculate confidence based on sources
                confidence = self._calculate_confidence(source_docs, answer)
                
                # Format sources
                sources = self._format_sources(source_docs)
                
            else:
                # Fallback if QA chain not initialized
                logger.warning("QA chain not initialized, using fallback")
                recommendations = self._get_fallback_recommendations(incident)
                confidence = 0.5
                sources = []
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            """ return {
                "recommendations": recommendations,
                "confidence": confidence,
                "sources": sources,
                "processing_time": processing_time,
                "metadata": {
                    "langchain_version": "0.1.16",
                    "model": self.config.get('model', 'llama3.2:3b')
                }
            } """
            
            # FIXED: Wrap response in RAGResponse object
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
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the vector store
        """
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return
        
        # Convert to LangChain documents
        langchain_docs = []
        for doc in documents:
            content = f"{doc.get('title', '')} {doc.get('description', '')} {doc.get('resolution', '')}"
            
            # Split into chunks
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                langchain_docs.append(Document(
                    page_content=chunk,
                    metadata={
                        "id": f"{doc.get('id', '')}_{i}",
                        "title": doc.get('title', ''),
                        "category": doc.get('category', ''),
                        "chunk_index": i
                    }
                ))
        
        # Add to vector store
        if langchain_docs:
            self.vector_store.add_documents(langchain_docs)
            logger.info(f"Added {len(langchain_docs)} document chunks to vector store")
    
    def _prepare_query(self, incident: Incident) -> str:
        """Prepare query from incident"""
        query_parts = [
            f"Title: {incident.title}",
            f"Description: {incident.description}",
            f"Priority: {incident.priority}",
            f"Category: {incident.category}"
        ]
        
        if incident.error_message:
            query_parts.append(f"Error: {incident.error_message}")
        
        if incident.affected_systems:
            query_parts.append(f"Affected Systems: {', '.join(incident.affected_systems)}")
        
        return "\n".join(query_parts)
    
    def _parse_answer_to_recommendations(self, answer: str) -> List[Dict[str, Any]]:
        """Parse LLM answer into structured recommendations"""
        try:
            # Try to extract structured sections from the answer
            recommendations = []
            
            # Create primary recommendation
            primary = {
                "type": "primary",
                "solution_steps": [],
                "root_cause": "",
                "prevention": "",
                "escalation": "",
                "confidence": 0.8
            }
            
            # Simple parsing - look for numbered steps
            lines = answer.split('\n')
            current_section = "solution"
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if 'root cause' in line.lower():
                    current_section = "root_cause"
                elif 'prevention' in line.lower() or 'prevent' in line.lower():
                    current_section = "prevention"
                elif 'escalat' in line.lower():
                    current_section = "escalation"
                elif line[0:2] in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']:
                    primary["solution_steps"].append(line)
                elif current_section == "root_cause":
                    primary["root_cause"] += " " + line
                elif current_section == "prevention":
                    primary["prevention"] += " " + line
                elif current_section == "escalation":
                    primary["escalation"] += " " + line
            
            # Ensure we have at least some solution steps
            if not primary["solution_steps"]:
                primary["solution_steps"] = [answer[:200]]
            
            recommendations.append(primary)
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to parse answer: {e}")
            return [{
                "type": "primary",
                "solution_steps": [answer],
                "confidence": 0.5
            }]
    
    def _calculate_confidence(self, source_docs: List, answer: str) -> float:
        """Calculate confidence based on sources and answer quality"""
        if not source_docs:
            return 0.3
        
        # Basic confidence calculation
        base_confidence = min(len(source_docs) / 5, 1.0) * 0.5
        
        # Check answer quality
        if len(answer) > 100 and any(word in answer.lower() for word in ['step', 'solution', 'resolve']):
            base_confidence += 0.3
        
        # Check if answer seems complete
        if all(section in answer.lower() for section in ['root cause', 'prevent']):
            base_confidence += 0.2
        
        return min(base_confidence, 0.95)
    
    def _format_sources(self, source_docs: List) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        sources = []
        for i, doc in enumerate(source_docs[:5]):  # Limit to top 5
            sources.append({
                "id": doc.metadata.get('id', f'source_{i}'),
                "title": doc.metadata.get('title', 'Unknown'),
                "category": doc.metadata.get('category', 'general'),
                "preview": doc.page_content[:200] + "...",
                "relevance_score": 0.8 - (i * 0.1)  # Decreasing relevance
            })
        return sources
    
    def _get_fallback_recommendations(self, incident: Incident) -> List[Dict[str, Any]]:
        """Fallback recommendations when LangChain fails"""
        return [{
            "type": "primary",
            "solution_steps": [
                "1. Review system logs for errors",
                "2. Check service status and health",
                "3. Verify configuration settings",
                "4. Restart affected services if needed",
                "5. Monitor for 15 minutes",
                "6. Escalate if issue persists"
            ],
            "root_cause": "Unable to determine - requires investigation",
            "prevention": "Implement monitoring and alerting",
            "confidence": 0.4
        }]
    
    # def _get_error_response(self, incident: Incident, error: str) -> Dict[str, Any]:
        """Return error response"""
        """ return {
            "recommendations": self._get_fallback_recommendations(incident),
            "confidence": 0.3,
            "sources": [],
            "processing_time": 0,
            "metadata": {
                "error": error,
                "fallback": True
            }
        } """
    
    def _get_error_response(self, incident: Incident, error: str) -> RAGResponse:  # Changed return type
        """Return error response"""
        response = RAGResponse(
            recommendations=self._get_fallback_recommendations(incident),
            confidence=0.3,
            sources=[],
            processing_time=0
        )
        response.metadata = {
            "error": error,
            "fallback": True
        }
        return response
    
# Alias for compatibility with imports
RAGAgent = LangChainRAGAgent
__all__ = ['RAGAgent', 'LangChainRAGAgent', 'RAGResponse']  # ADD THIS LINE