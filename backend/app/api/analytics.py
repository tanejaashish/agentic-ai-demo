"""
API routes for analytics and metrics
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """
    Get current system metrics
    """
    # Generate demo metrics
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "incidents": {
            "total_processed": random.randint(1000, 2000),
            "last_24h": random.randint(50, 150),
            "last_hour": random.randint(5, 20),
            "average_processing_time": round(random.uniform(1.5, 3.5), 2)
        },
        "agents": {
            "rag": {
                "status": "active",
                "processed": random.randint(900, 1900),
                "average_confidence": round(random.uniform(0.7, 0.95), 2)
            },
            "cag": {
                "status": "active",
                "triggered_rate": round(random.uniform(0.2, 0.4), 2),
                "average_iterations": round(random.uniform(1.5, 2.5), 1)
            },
            "predictive": {
                "status": "active",
                "accuracy": round(random.uniform(0.8, 0.95), 2)
            }
        },
        "performance": {
            "api_latency_ms": random.randint(50, 200),
            "vector_search_ms": random.randint(20, 80),
            "llm_generation_ms": random.randint(500, 2000)
        }
    }

@router.get("/trends")
async def get_trends(
    days: int = Query(7, ge=1, le=30)
):
    """
    Get trend data for the specified number of days
    """
    trends = []
    base_date = datetime.utcnow() - timedelta(days=days)
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        trends.append({
            "date": date.isoformat(),
            "incidents": random.randint(80, 150),
            "resolved": random.randint(70, 140),
            "average_resolution_time": random.randint(30, 90),
            "cag_applications": random.randint(20, 50)
        })
    
    return {
        "period": f"{days} days",
        "data": trends
    }

@router.get("/performance")
async def get_performance_metrics():
    """
    Get detailed performance metrics
    """
    return {
        "rag_performance": {
            "retrieval": {
                "average_documents": 5,
                "average_similarity": 0.82,
                "cache_hit_rate": 0.65
            },
            "generation": {
                "average_tokens": 256,
                "average_time_ms": 1200
            }
        },
        "cag_performance": {
            "trigger_rate": 0.32,
            "average_iterations": 2.1,
            "confidence_improvement": 0.18,
            "success_rate": 0.91
        },
        "prediction_performance": {
            "severity_accuracy": 0.86,
            "time_mae": 12.5,  # Mean Absolute Error in minutes
            "team_accuracy": 0.79
        }
    }

@router.get("/feedback-stats")
async def get_feedback_statistics():
    """
    Get feedback statistics
    """
    return {
        "total_feedback": random.randint(500, 1000),
        "average_rating": round(random.uniform(3.8, 4.5), 1),
        "ratings_distribution": {
            "1": random.randint(5, 20),
            "2": random.randint(10, 30),
            "3": random.randint(50, 100),
            "4": random.randint(100, 200),
            "5": random.randint(150, 300)
        },
        "helpful_percentage": round(random.uniform(0.75, 0.92), 2)
    }

@router.get("/resource-usage")
async def get_resource_usage():
    """
    Get system resource usage
    """
    return {
        "cpu": {
            "usage_percent": round(random.uniform(20, 60), 1),
            "cores_available": 4,
            "cores_used": round(random.uniform(1, 3), 1)
        },
        "memory": {
            "total_gb": 16,
            "used_gb": round(random.uniform(4, 10), 1),
            "cache_mb": random.randint(200, 800)
        },
        "storage": {
            "vector_db_gb": round(random.uniform(0.5, 2), 1),
            "logs_mb": random.randint(100, 500),
            "models_gb": 4.2
        }
    }