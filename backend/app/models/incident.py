"""
Data models for incident management system
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class Priority(str, Enum):
    """Incident priority levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class Category(str, Enum):
    """Incident categories"""
    GENERAL = "General"
    DATABASE = "Database"
    NETWORK = "Network"
    APPLICATION = "Application"
    SECURITY = "Security"
    INFRASTRUCTURE = "Infrastructure"
    AUTHENTICATION = "Authentication"
    DATA_PROCESSING = "Data Processing"
    MOBILE = "Mobile"
    SEARCH = "Search"
    COMMUNICATION = "Communication"
    PERFORMANCE = "Performance"
    CACHE = "Cache"

class Incident(BaseModel):
    """Incident request model"""
    id: Optional[str] = Field(None, description="Unique incident identifier")
    title: str = Field(..., min_length=5, max_length=200, description="Brief incident title")
    description: str = Field(..., min_length=10, description="Detailed description")
    priority: Priority = Field(Priority.MEDIUM, description="Incident priority")
    category: Category = Field(Category.GENERAL, description="Incident category")
    error_message: Optional[str] = Field(None, description="Specific error message if available")
    affected_systems: List[str] = Field(default_factory=list, description="List of affected systems")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    @validator('affected_systems')
    def validate_systems(cls, v):
        """Ensure affected systems list is not too large"""
        if len(v) > 20:
            raise ValueError("Too many affected systems (max 20)")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "INC12345",
                "title": "Database connection timeout in production",
                "description": "Users experiencing timeout errors when accessing the customer portal",
                "priority": "High",
                "category": "Database",
                "error_message": "Connection pool exhausted",
                "affected_systems": ["MySQL", "Customer Portal", "API Gateway"]
            }
        }

class Recommendation(BaseModel):
    """Single recommendation from the AI system"""
    type: str = Field(..., description="Type of recommendation (primary/alternative)")
    solution_steps: List[str] = Field(..., description="Step-by-step solution")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    root_cause: Optional[str] = Field(None, description="Identified root cause")
    prevention: Optional[str] = Field(None, description="Prevention measures")
    escalation: Optional[str] = Field(None, description="Escalation criteria")
    source_ids: List[str] = Field(default_factory=list, description="Source document IDs")

class Source(BaseModel):
    """Knowledge source reference"""
    id: str
    title: str
    relevance_score: float
    category: str
    preview: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IncidentResponse(BaseModel):
    """Complete response for an incident"""
    incident_id: str
    recommendations: List[Recommendation]
    confidence: float = Field(..., ge=0, le=1)
    severity: str = Field(..., description="Predicted severity")
    estimated_resolution_time: int = Field(..., description="Estimated resolution time in minutes")
    assigned_team: str = Field(..., description="Recommended team assignment")
    rag_sources: List[Source] = Field(default_factory=list)
    cag_applied: bool = Field(False, description="Whether CAG refinement was applied")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "incident_id": "INC12345",
                "recommendations": [
                    {
                        "type": "primary",
                        "solution_steps": [
                            "Check connection pool configuration",
                            "Increase pool size from 50 to 100",
                            "Restart application server"
                        ],
                        "confidence": 0.92,
                        "root_cause": "Connection pool undersized for current load",
                        "prevention": "Implement auto-scaling for connection pools",
                        "source_ids": ["KB001", "INC008"]
                    }
                ],
                "confidence": 0.85,
                "severity": "High",
                "estimated_resolution_time": 45,
                "assigned_team": "Database Team",
                "cag_applied": True,
                "processing_time": 2.34
            }
        }

class FeedbackRequest(BaseModel):
    """User feedback on recommendations"""
    incident_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    helpful: bool = Field(..., description="Was the recommendation helpful?")
    comments: Optional[str] = Field(None, description="Additional comments")
    applied_solution: Optional[int] = Field(None, description="Index of applied solution")
    resolution_time_actual: Optional[int] = Field(None, description="Actual resolution time")
    
    class Config:
        schema_extra = {
            "example": {
                "incident_id": "INC12345",
                "rating": 5,
                "helpful": True,
                "comments": "Solution worked perfectly",
                "applied_solution": 0,
                "resolution_time_actual": 30
            }
        }

class MetricsResponse(BaseModel):
    """System metrics response"""
    total_incidents: int
    average_confidence: float
    average_resolution_time: float
    cag_improvement_rate: float
    top_categories: List[Dict[str, Any]]
    success_rate: float
    active_agents: int
    
class AgentStatus(BaseModel):
    """Status of an individual agent"""
    name: str
    status: str  # active, idle, processing, error
    current_task: Optional[str]
    processed_count: int
    average_processing_time: float
    last_activity: datetime

class SystemHealth(BaseModel):
    """System health status"""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    services: Dict[str, bool]
    metrics: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class KnowledgeArticle(BaseModel):
    """Knowledge base article"""
    id: str
    title: str
    category: str
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    usage_count: int = Field(0)
    effectiveness_score: Optional[float] = Field(None, ge=0, le=1)

class TrainingData(BaseModel):
    """Training data for model updates"""
    incident: Incident
    resolution: str
    success: bool
    resolution_time: int
    feedback: Optional[FeedbackRequest]
    
class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., min_length=3, description="Search query text")
    category: Optional[Category] = Field(None, description="Filter by category")
    priority: Optional[Priority] = Field(None, description="Filter by priority")
    limit: int = Field(10, ge=1, le=50, description="Maximum results")
    include_knowledge: bool = Field(True, description="Include knowledge base articles")