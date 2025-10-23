"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime

from app.models.incident import Incident, Priority, Category
from app.services.llm_service import LLMService
from app.utils.advanced_metrics import AdvancedMetricsCollector
from app.utils.circuit_breaker import CircuitBreakerManager


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_incident() -> Incident:
    """Create a sample incident for testing"""
    return Incident(
        id="test-001",
        title="Database connection timeout",
        description="Application cannot connect to the database after deployment",
        priority=Priority.HIGH,
        category=Category.DATABASE,
        error_message="Connection timeout after 30s",
        affected_systems=["api-server", "database"],
        timestamp=datetime.now()
    )


@pytest.fixture
def vague_incident() -> Incident:
    """Create a vague incident for CAG testing"""
    return Incident(
        id="test-002",
        title="Application is slow",
        description="Users are reporting that the application is slow",
        priority=Priority.MEDIUM,
        category=Category.PERFORMANCE,
        affected_systems=["web-app"],
        timestamp=datetime.now()
    )


@pytest.fixture
def mock_llm_service() -> LLMService:
    """Create a mock LLM service for testing"""
    class MockLLM:
        async def generate(self, prompt: str, **kwargs):
            # Return mock responses based on prompt keywords
            if "critique" in prompt.lower() or "issues" in prompt.lower():
                return "Missing error details\nUnclear resolution steps\nNo prevention measures"
            elif "correction" in prompt.lower():
                return '[{"issue_number": 1, "correction_type": "addition", "target_field": "solution_steps", "correction_content": "Add detailed steps", "rationale": "Improve clarity"}]'
            elif "score" in prompt.lower() or "rate" in prompt.lower():
                return "75"
            else:
                return "Mock LLM response"

    return MockLLM()


@pytest.fixture
def metrics_collector() -> AdvancedMetricsCollector:
    """Create a fresh metrics collector for testing"""
    collector = AdvancedMetricsCollector(config={'enabled': True})
    yield collector
    collector.reset()


@pytest.fixture
def circuit_breaker_manager() -> CircuitBreakerManager:
    """Create a circuit breaker manager for testing"""
    return CircuitBreakerManager()


@pytest.fixture
def sample_documents() -> list:
    """Sample documents for vector store testing"""
    return [
        {
            "id": "doc-001",
            "content": "To fix database connection timeouts, increase the connection pool size and timeout values",
            "title": "Database Connection Timeout Fix",
            "category": "database",
            "metadata": {"tags": ["database", "timeout", "connection"]}
        },
        {
            "id": "doc-002",
            "content": "Performance issues can be resolved by optimizing database queries and adding indexes",
            "title": "Performance Optimization Guide",
            "category": "performance",
            "metadata": {"tags": ["performance", "database", "optimization"]}
        },
        {
            "id": "doc-003",
            "content": "API gateway 502 errors are often caused by backend service timeouts or unavailability",
            "title": "API Gateway 502 Error Troubleshooting",
            "category": "api",
            "metadata": {"tags": ["api", "502", "gateway"]}
        }
    ]


@pytest.fixture
def sample_rag_response() -> Dict[str, Any]:
    """Sample RAG response for CAG testing"""
    return {
        "recommendations": [
            {
                "solution_steps": [
                    "Check database connection pool configuration",
                    "Increase timeout values",
                    "Monitor connection pool usage"
                ],
                "root_cause": "Database connection pool exhaustion",
                "confidence": 0.65
            }
        ],
        "confidence": 0.65,
        "sources": [
            {
                "id": "doc-001",
                "title": "Database Connection Timeout Fix",
                "score": 0.85
            }
        ],
        "metadata": {
            "processing_time": 1.23
        }
    }


@pytest.fixture
def sample_feedback_records() -> list:
    """Sample feedback records for learning pipeline"""
    return [
        {
            "incident_id": "test-001",
            "recommendation_id": "rec-001",
            "feedback_type": "positive",
            "rating": 4.5,
            "comment": "Solution worked great"
        },
        {
            "incident_id": "test-002",
            "recommendation_id": "rec-002",
            "feedback_type": "negative",
            "rating": 2.0,
            "comment": "Did not solve the issue"
        },
        {
            "incident_id": "test-003",
            "recommendation_id": "rec-003",
            "feedback_type": "positive",
            "rating": 5.0,
            "comment": "Excellent solution"
        }
    ]
