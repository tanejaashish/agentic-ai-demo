"""
API routes for incident management
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime

from app.models.incident import (
    Incident, IncidentResponse, FeedbackRequest,
    SearchQuery, Priority, Category
)
from app.config import settings

router = APIRouter()

# In-memory storage for demo (would use database in production)
incidents_store = []
feedback_store = []

@router.post("/", response_model=IncidentResponse)
async def create_incident(incident: Incident):
    """
    Create and process a new incident
    """
    # This endpoint is handled by the main process_incident endpoint
    # Included here for RESTful API completeness
    raise HTTPException(
        status_code=501,
        detail="Use /api/process-incident endpoint for incident processing"
    )

@router.get("/", response_model=List[Incident])
async def list_incidents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    priority: Optional[Priority] = None,
    category: Optional[Category] = None
):
    """
    List all incidents with optional filtering
    """
    filtered = incidents_store
    
    if priority:
        filtered = [i for i in filtered if i.get("priority") == priority.value]
    
    if category:
        filtered = [i for i in filtered if i.get("category") == category.value]
    
    return filtered[offset:offset + limit]

@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """
    Get a specific incident by ID
    """
    for incident in incidents_store:
        if incident.get("id") == incident_id:
            return incident
    
    raise HTTPException(status_code=404, detail="Incident not found")

@router.post("/search", response_model=List[IncidentResponse])
async def search_incidents(query: SearchQuery):
    """
    Search incidents using natural language query
    """
    # Simplified search for demo
    results = []
    
    for incident in incidents_store:
        # Check if query matches title or description
        if query.query.lower() in incident.get("title", "").lower() or \
           query.query.lower() in incident.get("description", "").lower():
            
            # Apply filters
            if query.priority and incident.get("priority") != query.priority.value:
                continue
            if query.category and incident.get("category") != query.category.value:
                continue
            
            results.append(incident)
            
            if len(results) >= query.limit:
                break
    
    return results

@router.post("/{incident_id}/feedback")
async def submit_incident_feedback(
    incident_id: str,
    feedback: FeedbackRequest
):
    """
    Submit feedback for an incident resolution
    """
    # Verify incident exists
    incident_exists = any(i.get("id") == incident_id for i in incidents_store)
    if not incident_exists:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Store feedback
    feedback_data = feedback.dict()
    feedback_data["incident_id"] = incident_id
    feedback_data["timestamp"] = datetime.utcnow().isoformat()
    feedback_store.append(feedback_data)
    
    return {"status": "success", "message": "Feedback recorded"}

@router.get("/{incident_id}/similar")
async def get_similar_incidents(
    incident_id: str,
    limit: int = Query(5, ge=1, le=20)
):
    """
    Get similar incidents based on the given incident
    """
    # This would use vector similarity in production
    # For demo, return random incidents
    similar = [
        incident for incident in incidents_store
        if incident.get("id") != incident_id
    ][:limit]
    
    return {
        "incident_id": incident_id,
        "similar_incidents": similar,
        "similarity_method": "vector_cosine"
    }

@router.get("/stats/summary")
async def get_incidents_summary():
    """
    Get summary statistics of incidents
    """
    total = len(incidents_store)
    
    if total == 0:
        return {
            "total_incidents": 0,
            "by_priority": {},
            "by_category": {},
            "average_resolution_time": 0
        }
    
    # Calculate statistics
    priority_counts = {}
    category_counts = {}
    resolution_times = []
    
    for incident in incidents_store:
        # Priority counts
        priority = incident.get("priority", "unknown")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Category counts
        category = incident.get("category", "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # Resolution times
        if "resolution_time" in incident:
            resolution_times.append(incident["resolution_time"])
    
    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    
    return {
        "total_incidents": total,
        "by_priority": priority_counts,
        "by_category": category_counts,
        "average_resolution_time": avg_resolution,
        "total_feedback": len(feedback_store)
    }