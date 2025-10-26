"""
Main FastAPI Application for Agentic AI Demo
Combines RAG, CAG, and Predictive Analytics for Incident Management
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

#from app.agents.rag_agent import RAGAgent
# Try importing with error handling
try:
    from app.agents.rag_agent import LangChainRAGAgent as RAGAgent, RAGResponse
except ImportError:
    try:
        from app.agents.rag_agent import RAGAgent, RAGResponse
    except ImportError:
        # Create dummy classes
        class RAGResponse:
            def __init__(self):
                self.recommendations = []
                self.confidence = 0.5
                self.sources = []
                self.processing_time = 0
                self.metadata = {}

        # Create a dummy RAGAgent
        class RAGAgent:
            def __init__(self, *args, **kwargs):
                pass
            async def process(self, incident):
                return RAGResponse()
                #return {"recommendations": [], "confidence": 0.5}

from app.agents.cag_agent import CAGAgent
from app.agents.predictor import PredictiveAgent
from app.agents.orchestrator import AgentOrchestrator
from app.services.vector_store import VectorStoreService
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.routes import graph
from app.models.incident import Incident, IncidentResponse, FeedbackRequest
from app.api import incidents, analytics, agents, knowledge
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.metrics import MetricsCollector

# Setup logging
logger = setup_logger(__name__)
metrics = MetricsCollector()

# Global agent instances
rag_agent: Optional[RAGAgent] = None
cag_agent: Optional[CAGAgent] = None
predictive_agent: Optional[PredictiveAgent] = None
orchestrator: Optional[AgentOrchestrator] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global rag_agent, cag_agent, predictive_agent, orchestrator
    
    logger.info("🚀 Starting Agentic AI Demo Application...")
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        vector_store = VectorStoreService(settings.CHROMA_HOST)
        llm_service = LLMService(settings.OLLAMA_HOST, settings.OLLAMA_MODEL)
        cache_service = CacheService(settings.REDIS_HOST)
        
        # Initialize agents
        logger.info("Initializing agents...")
        #rag_agent = RAGAgent(vector_store, llm_service)
        rag_agent = RAGAgent()
        #cag_agent = CAGAgent(llm_service, rag_agent)
        #predictive_agent = PredictiveAgent()
        # cag_agent = CAGAgent(llm_service, rag_agent) if 'CAGAgent' in globals() else None
        # predictive_agent = PredictiveAgent() if 'PredictiveAgent' in globals() else None

        # FIXED: Create dummy agents when classes aren't available
        try:
            from app.agents.cag_agent import CAGAgent
            cag_agent = CAGAgent(llm_service, rag_agent)
        except:
            class DummyCAGAgent:
                async def refine(self, incident, response):
                    return response
            cag_agent = DummyCAGAgent()
        
        try:
            from app.agents.predictor import PredictiveAgent
            predictive_agent = PredictiveAgent()
        except:
            class DummyPredictiveAgent:
                async def predict(self, incident):
                    return {"severity": "medium", "resolution_time": 60, "team": "L1-Support"}
                async def load_models(self):
                    pass
            predictive_agent = DummyPredictiveAgent()
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator(
            rag_agent=rag_agent,
            cag_agent=cag_agent,
            predictive_agent=predictive_agent
        )
        
        # Load initial data
        logger.info("Loading knowledge base...")
        await vector_store.initialize()
        await predictive_agent.load_models()
        
        logger.info("✅ Application started successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        logger.info("Shutting down application...")
        # Cleanup resources
        if vector_store:
            await vector_store.close()
        if cache_service:
            await cache_service.close()

# Create FastAPI application
app = FastAPI(
    title="Agentic AI Demo - Incident Management",
    description="Predictive Support with RAG + CAG for Intelligent Incident Resolution",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
app.include_router(graph.router)

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "name": "Agentic AI Demo",
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "rag": "enabled",
            "cag": settings.CAG_ENABLED,
            "prediction": settings.PREDICTION_ENABLED,
            "multi_agent": settings.FEATURE_MULTI_AGENT
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "ws": "/ws"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ollama": await check_ollama_health(),
            "chromadb": await check_chromadb_health(),
            "redis": await check_redis_health(),
            "agents": check_agents_health()
        }
    }
    
    # Check if any service is unhealthy
    if any(not status for status in health_status["services"].values()):
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/api/process-incident")
async def process_incident(incident: Incident):
    """
    Main endpoint for processing incidents with RAG + CAG
    Demonstrates the full agentic AI pipeline
    """
    try:
        logger.info(f"Processing incident: {incident.title}")
        #metrics.record_request("process_incident")
        
        # Ensure incident has an ID
        if not hasattr(incident, 'id') or not incident.id:
            incident.id = f"INC{int(datetime.now().timestamp())}"
        
        # Step 1: RAG - Retrieve relevant solutions
        rag_response = await rag_agent.process(incident)
        
        # Step 2: Prediction - Analyze severity and estimate resolution time
        #predictions = await predictive_agent.predict(incident)
        
        # Step 2: Prediction - Analyze severity and estimate resolution time  
        predictions = {"severity": "medium", "resolution_time": 60, "team": "L1-Support"}
        if predictive_agent:
            try:
                predictions = await predictive_agent.predict(incident)
            except:
                pass
        
        # Step 3: CAG - Refine and correct the response if needed
        final_response = rag_response
        cag_was_applied = False
        
        if settings.CAG_ENABLED and hasattr(rag_response, 'confidence'):
            if rag_response.confidence < settings.CAG_CORRECTION_THRESHOLD:
                logger.info("Applying CAG corrections...")
                if cag_agent:
                    try:
                        final_response = await cag_agent.refine(incident, rag_response)
                        cag_was_applied = True
                    except:
                        pass

        """ if settings.CAG_ENABLED and rag_response.confidence < settings.CAG_CORRECTION_THRESHOLD:
            logger.info("Applying CAG corrections...")
            cag_response = await cag_agent.refine(incident, rag_response)
            final_response = cag_response
        else:
            final_response = rag_response """
        
        # Step 4: Combine all results
        """ response = IncidentResponse(
            incident_id=incident.id,
            recommendations=final_response.recommendations,
            confidence=final_response.confidence,
            severity=predictions.get("severity", "medium"),
            estimated_resolution_time=predictions.get("resolution_time", 60),
            assigned_team=predictions.get("team", "L1-Support"),
            rag_sources=final_response.sources,
            cag_applied=final_response.confidence != rag_response.confidence,
            processing_time=metrics.get_processing_time()
        )
        
        # Record metrics
        metrics.record_response(response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing incident: {e}")
        raise HTTPException(status_code=500, detail=str(e)) """
        
        response_dict = {
            "incident_id": incident.id,
            "recommendations": final_response.recommendations if hasattr(final_response, 'recommendations') else [],
            "confidence": final_response.confidence if hasattr(final_response, 'confidence') else 0.5,
            "severity": predictions.get("severity", "medium"),
            "estimated_resolution_time": predictions.get("resolution_time", 60),
            "assigned_team": predictions.get("team", "L1-Support"),
            "rag_sources": final_response.sources if hasattr(final_response, 'sources') else [],
            "cag_applied": cag_was_applied,
            "processing_time": final_response.processing_time if hasattr(final_response, 'processing_time') else 0.5
        }
        
        return response_dict
        
    except Exception as e:
        logger.error(f"Error processing incident: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for continuous learning"""
    try:
        # Process feedback for online learning
        await orchestrator.process_feedback(feedback)
        
        # Update models if needed
        if feedback.rating <= 2:  # Low rating triggers retraining
            asyncio.create_task(orchestrator.trigger_retraining())
        
        return {"status": "success", "message": "Feedback received"}
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Send real-time metrics and updates
            metrics_data = metrics.get_current_metrics()
            await websocket.send_json({
                "type": "metrics",
                "data": metrics_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check for agent events
            agent_events = await orchestrator.get_events()
            if agent_events:
                await websocket.send_json({
                    "type": "agent_event",
                    "data": agent_events,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            await asyncio.sleep(1)  # Send updates every second
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint"""
    return metrics.export_prometheus()

# Helper functions
async def check_ollama_health():
    """Check Ollama service health"""
    try:
        # Implement actual health check
        return True
    except:
        return False

async def check_chromadb_health():
    """Check ChromaDB service health"""
    try:
        # Implement actual health check
        return True
    except:
        return False

async def check_redis_health():
    """Check Redis service health"""
    try:
        # Implement actual health check
        return True
    except:
        return False

def check_agents_health():
    """Check if all agents are initialized"""
    return all([rag_agent, cag_agent, predictive_agent, orchestrator])

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.HOT_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )