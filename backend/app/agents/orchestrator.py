"""
Agent Orchestrator - Coordinates multiple agents for incident processing
Manages the flow between RAG, CAG, and Predictive agents
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum
import json

from app.agents.rag_agent import RAGAgent, RAGResponse
from app.agents.cag_agent import CAGAgent, CAGResponse
from app.agents.predictor import PredictiveAgent
from app.models.incident import Incident, FeedbackRequest

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Stages of incident processing"""
    INITIALIZATION = "initialization"
    RAG_RETRIEVAL = "rag_retrieval"
    RAG_GENERATION = "rag_generation"
    PREDICTION = "prediction"
    CAG_EVALUATION = "cag_evaluation"
    CAG_REFINEMENT = "cag_refinement"
    FINALIZATION = "finalization"
    COMPLETED = "completed"

@dataclass
class ProcessingEvent:
    """Event during processing for real-time updates"""
    stage: ProcessingStage
    message: str
    progress: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: Dict[str, Any]

class AgentOrchestrator:
    """
    Orchestrates multiple agents to process incidents
    Manages coordination, communication, and workflow
    """
    
    def __init__(
        self,
        rag_agent: RAGAgent,
        cag_agent: CAGAgent,
        predictive_agent: PredictiveAgent,
        config: Optional[Dict] = None
    ):
        self.rag_agent = rag_agent
        self.cag_agent = cag_agent
        self.predictive_agent = predictive_agent
        
        # Configuration
        self.config = config or {}
        self.enable_cag = self.config.get('enable_cag', True)
        self.cag_threshold = self.config.get('cag_threshold', 0.7)
        self.enable_prediction = self.config.get('enable_prediction', True)
        self.parallel_processing = self.config.get('parallel_processing', True)
        
        # Event tracking
        self.events_queue = asyncio.Queue()
        self.processing_history = []
        
        # Metrics
        self.total_processed = 0
        self.total_cag_applied = 0
        self.average_confidence = 0.0
        
        logger.info("Agent Orchestrator initialized with %s agents", 
                   sum([1 for a in [rag_agent, cag_agent, predictive_agent] if a]))
    
    async def process_incident(
        self,
        incident: Incident,
        stream_events: bool = True
    ) -> Dict[str, Any]:
        """
        Main orchestration method - coordinates all agents
        """
        start_time = datetime.now()
        self.total_processed += 1
        
        try:
            # Initialize processing
            await self._emit_event(ProcessingEvent(
                stage=ProcessingStage.INITIALIZATION,
                message="Starting incident processing",
                progress=0.0,
                timestamp=datetime.now(),
                metadata={"incident_id": incident.id}
            ))
            
            # Stage 1: RAG Processing
            logger.info(f"Stage 1: RAG processing for incident {incident.id}")
            await self._emit_event(ProcessingEvent(
                stage=ProcessingStage.RAG_RETRIEVAL,
                message="Retrieving similar incidents from knowledge base",
                progress=0.2,
                timestamp=datetime.now(),
                metadata={"top_k": self.rag_agent.top_k}
            ))
            
            rag_response = await self.rag_agent.process(incident)
            
            await self._emit_event(ProcessingEvent(
                stage=ProcessingStage.RAG_GENERATION,
                message=f"Generated recommendations with {len(rag_response.sources)} sources",
                progress=0.4,
                timestamp=datetime.now(),
                metadata={
                    "sources_found": len(rag_response.sources),
                    "initial_confidence": rag_response.confidence
                }
            ))
            
            # Stage 2: Predictive Analytics (can run in parallel)
            predictions = None
            if self.enable_prediction:
                logger.info("Stage 2: Predictive analytics")
                await self._emit_event(ProcessingEvent(
                    stage=ProcessingStage.PREDICTION,
                    message="Analyzing incident patterns and predicting metrics",
                    progress=0.5,
                    timestamp=datetime.now(),
                    metadata={}
                ))
                
                if self.parallel_processing:
                    # Run prediction in parallel with CAG
                    prediction_task = asyncio.create_task(
                        self.predictive_agent.predict(incident)
                    )
                else:
                    predictions = await self.predictive_agent.predict(incident)
            
            # Stage 3: CAG Refinement (if needed)
            final_response = rag_response
            cag_applied = False
            
            if self.enable_cag and rag_response.confidence < self.cag_threshold:
                logger.info(f"Stage 3: CAG refinement (confidence {rag_response.confidence:.2f} < {self.cag_threshold})")
                
                await self._emit_event(ProcessingEvent(
                    stage=ProcessingStage.CAG_EVALUATION,
                    message=f"Response confidence low ({rag_response.confidence:.2f}), applying CAG",
                    progress=0.6,
                    timestamp=datetime.now(),
                    metadata={"reason": "low_confidence"}
                ))
                
                cag_response = await self.cag_agent.refine(incident, rag_response)
                
                await self._emit_event(ProcessingEvent(
                    stage=ProcessingStage.CAG_REFINEMENT,
                    message=f"Refined response through {cag_response.total_iterations} iterations",
                    progress=0.8,
                    timestamp=datetime.now(),
                    metadata={
                        "iterations": cag_response.total_iterations,
                        "improvement": f"{cag_response.improvement_percentage:.1f}%"
                    }
                ))
                
                # Convert CAG response to RAG-like format for consistency
                final_response = self._merge_responses(rag_response, cag_response)
                cag_applied = True
                self.total_cag_applied += 1
            
            # Wait for prediction if it was running in parallel
            if self.enable_prediction and self.parallel_processing and not predictions:
                predictions = await prediction_task
            
            # Stage 4: Finalize response
            await self._emit_event(ProcessingEvent(
                stage=ProcessingStage.FINALIZATION,
                message="Preparing final response",
                progress=0.9,
                timestamp=datetime.now(),
                metadata={}
            ))
            
            # Combine all results
            orchestrated_response = self._create_final_response(
                incident=incident,
                rag_response=final_response,
                predictions=predictions,
                cag_applied=cag_applied,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Update metrics
            self._update_metrics(orchestrated_response)
            
            # Final event
            await self._emit_event(ProcessingEvent(
                stage=ProcessingStage.COMPLETED,
                message="Processing completed successfully",
                progress=1.0,
                timestamp=datetime.now(),
                metadata={
                    "total_time": orchestrated_response["processing_time"],
                    "confidence": orchestrated_response["confidence"]
                }
            ))
            
            logger.info(f"Orchestration completed in {orchestrated_response['processing_time']:.2f}s")
            return orchestrated_response
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            await self._emit_event(ProcessingEvent(
                stage=ProcessingStage.COMPLETED,
                message=f"Processing failed: {str(e)}",
                progress=1.0,
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            ))
            raise
    
    async def process_feedback(self, feedback: FeedbackRequest):
        """
        Process user feedback and trigger learning
        """
        logger.info(f"Processing feedback for incident {feedback.incident_id}: Rating {feedback.rating}")
        
        # Store feedback
        feedback_data = {
            "incident_id": feedback.incident_id,
            "rating": feedback.rating,
            "helpful": feedback.helpful,
            "timestamp": datetime.now().isoformat()
        }
        self.processing_history.append(feedback_data)
        
        # Trigger retraining if rating is low
        if feedback.rating <= 2:
            logger.info("Low rating received, scheduling model update")
            asyncio.create_task(self._trigger_model_update(feedback))
        
        # Update knowledge base if feedback is positive
        if feedback.rating >= 4 and feedback.helpful:
            logger.info("Positive feedback received, updating knowledge base")
            # This would update the vector store with successful resolution
    
    async def get_events(self) -> List[Dict[str, Any]]:
        """
        Get queued events for real-time updates
        """
        events = []
        while not self.events_queue.empty():
            try:
                event = await asyncio.wait_for(self.events_queue.get(), timeout=0.1)
                events.append(self._event_to_dict(event))
            except asyncio.TimeoutError:
                break
        return events
    
    async def trigger_retraining(self):
        """
        Trigger retraining of all models
        """
        logger.info("Triggering model retraining")
        
        # Collect training data from history
        if len(self.processing_history) < 10:
            logger.warning("Insufficient data for retraining")
            return
        
        # Prepare training data
        training_data = self._prepare_training_data()
        
        # Update each agent's models
        tasks = []
        if hasattr(self.predictive_agent, 'update_models'):
            tasks.append(self.predictive_agent.update_models(training_data))
        
        if tasks:
            await asyncio.gather(*tasks)
            logger.info("Model retraining completed")
    
    def _merge_responses(
        self,
        rag_response: RAGResponse,
        cag_response: CAGResponse
    ) -> RAGResponse:
        """
        Merge CAG improvements into RAG response format
        """
        # Create a new RAG response with CAG improvements
        return RAGResponse(
            recommendations=cag_response.final_recommendations,
            confidence=cag_response.final_confidence,
            sources=rag_response.sources,  # Keep original sources
            retrieval_time=rag_response.retrieval_time,
            generation_time=rag_response.generation_time + sum(
                it.confidence_after for it in cag_response.iterations
            ) * 0.5,  # Approximate additional time
            total_time=rag_response.total_time,
            metadata={
                **rag_response.metadata,
                "cag_iterations": cag_response.total_iterations,
                "cag_improvement": cag_response.improvement_percentage
            }
        )
    
    def _create_final_response(
        self,
        incident: Incident,
        rag_response: RAGResponse,
        predictions: Optional[Dict[str, Any]],
        cag_applied: bool,
        processing_time: float
    ) -> Dict[str, Any]:
        """
        Create the final orchestrated response
        """
        response = {
            "incident_id": incident.id,
            "recommendations": rag_response.recommendations,
            "confidence": rag_response.confidence,
            "rag_sources": rag_response.sources,
            "cag_applied": cag_applied,
            "processing_time": processing_time,
            "processing_stages": {
                "rag_retrieval": rag_response.retrieval_time,
                "rag_generation": rag_response.generation_time,
                "cag_refinement": rag_response.metadata.get("cag_iterations", 0) * 0.5 if cag_applied else 0
            }
        }
        
        # Add predictions if available
        if predictions:
            response.update({
                "severity": predictions.get("severity", "medium"),
                "severity_confidence": predictions.get("severity_confidence", 0.5),
                "estimated_resolution_time": predictions.get("resolution_time", 60),
                "assigned_team": predictions.get("team", "Support"),
                "risk_factors": predictions.get("risk_factors", []),
                "predictive_recommendations": predictions.get("recommendations", [])
            })
        else:
            # Default values if prediction is disabled
            response.update({
                "severity": "medium",
                "estimated_resolution_time": 60,
                "assigned_team": "L1-Support"
            })
        
        return response
    
    async def _emit_event(self, event: ProcessingEvent):
        """
        Emit a processing event for real-time updates
        """
        await self.events_queue.put(event)
        logger.debug(f"Event emitted: {event.stage.value} - {event.message}")
    
    def _event_to_dict(self, event: ProcessingEvent) -> Dict[str, Any]:
        """
        Convert event to dictionary for JSON serialization
        """
        return {
            "stage": event.stage.value,
            "message": event.message,
            "progress": event.progress,
            "timestamp": event.timestamp.isoformat(),
            "metadata": event.metadata
        }
    
    def _update_metrics(self, response: Dict[str, Any]):
        """
        Update orchestrator metrics
        """
        # Update running average confidence
        alpha = 0.1  # Exponential moving average factor
        self.average_confidence = (
            alpha * response["confidence"] +
            (1 - alpha) * self.average_confidence
        )
    
    async def _trigger_model_update(self, feedback: FeedbackRequest):
        """
        Trigger model update based on feedback
        """
        await asyncio.sleep(5)  # Debounce
        logger.info(f"Model update triggered by feedback on {feedback.incident_id}")
        # In production, this would queue a retraining job
    
    def _prepare_training_data(self) -> List[Dict[str, Any]]:
        """
        Prepare training data from processing history
        """
        training_data = []
        for record in self.processing_history[-100:]:  # Last 100 records
            if "rating" in record and record["rating"] >= 4:
                training_data.append({
                    "incident_id": record["incident_id"],
                    "success": True,
                    "confidence": record.get("confidence", 0.8)
                })
        return training_data
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status and metrics
        """
        return {
            "orchestrator": {
                "total_processed": self.total_processed,
                "cag_application_rate": self.total_cag_applied / max(self.total_processed, 1),
                "average_confidence": self.average_confidence,
                "agents_active": {
                    "rag": self.rag_agent is not None,
                    "cag": self.cag_agent is not None,
                    "predictive": self.predictive_agent is not None
                }
            },
            "configuration": {
                "cag_enabled": self.enable_cag,
                "cag_threshold": self.cag_threshold,
                "prediction_enabled": self.enable_prediction,
                "parallel_processing": self.parallel_processing
            },
            "performance": {
                "events_queued": self.events_queue.qsize(),
                "history_size": len(self.processing_history)
            }
        }