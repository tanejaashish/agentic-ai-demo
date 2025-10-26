"""
Knowledge Graph API Routes
Provides graph data, patterns, and relationships for visualization
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/data")
async def get_graph_data():
    """
    Get knowledge graph data for visualization
    Returns nodes and edges representing incidents, solutions, and relationships
    """
    try:
        # Generate demo graph data
        nodes = [
            # Incident categories
            {"id": "cat_database", "label": "Database Issues", "type": "category", "size": 30, "color": "#3b82f6"},
            {"id": "cat_network", "label": "Network Issues", "type": "category", "size": 25, "color": "#10b981"},
            {"id": "cat_application", "label": "Application Issues", "type": "category", "size": 28, "color": "#f59e0b"},
            
            # Specific incidents
            {"id": "inc_conn_pool", "label": "Connection Pool Exhausted", "type": "incident", "size": 20, "color": "#3b82f6"},
            {"id": "inc_timeout", "label": "Query Timeout", "type": "incident", "size": 18, "color": "#3b82f6"},
            {"id": "inc_deadlock", "label": "Deadlock Detected", "type": "incident", "size": 16, "color": "#3b82f6"},
            
            {"id": "inc_502", "label": "502 Bad Gateway", "type": "incident", "size": 22, "color": "#10b981"},
            {"id": "inc_dns", "label": "DNS Resolution Failed", "type": "incident", "size": 15, "color": "#10b981"},
            {"id": "inc_latency", "label": "High Network Latency", "type": "incident", "size": 17, "color": "#10b981"},
            
            {"id": "inc_memory", "label": "Memory Leak", "type": "incident", "size": 19, "color": "#f59e0b"},
            {"id": "inc_crash", "label": "Application Crash", "type": "incident", "size": 16, "color": "#f59e0b"},
            {"id": "inc_cpu", "label": "High CPU Usage", "type": "incident", "size": 14, "color": "#f59e0b"},
            
            # Solutions
            {"id": "sol_pool_size", "label": "Increase Pool Size", "type": "solution", "size": 15, "color": "#8b5cf6"},
            {"id": "sol_index", "label": "Add Database Index", "type": "solution", "size": 15, "color": "#8b5cf6"},
            {"id": "sol_restart", "label": "Restart Service", "type": "solution", "size": 12, "color": "#8b5cf6"},
            {"id": "sol_cache", "label": "Implement Caching", "type": "solution", "size": 14, "color": "#8b5cf6"},
            {"id": "sol_upgrade", "label": "Upgrade Infrastructure", "type": "solution", "size": 13, "color": "#8b5cf6"},
            
            # Systems
            {"id": "sys_mysql", "label": "MySQL", "type": "system", "size": 18, "color": "#ec4899"},
            {"id": "sys_api", "label": "API Gateway", "type": "system", "size": 20, "color": "#ec4899"},
            {"id": "sys_app", "label": "App Server", "type": "system", "size": 17, "color": "#ec4899"},
        ]
        
        edges = [
            # Category to incidents
            {"source": "cat_database", "target": "inc_conn_pool", "type": "contains", "weight": 3},
            {"source": "cat_database", "target": "inc_timeout", "type": "contains", "weight": 3},
            {"source": "cat_database", "target": "inc_deadlock", "type": "contains", "weight": 2},
            
            {"source": "cat_network", "target": "inc_502", "type": "contains", "weight": 3},
            {"source": "cat_network", "target": "inc_dns", "type": "contains", "weight": 2},
            {"source": "cat_network", "target": "inc_latency", "type": "contains", "weight": 2},
            
            {"source": "cat_application", "target": "inc_memory", "type": "contains", "weight": 3},
            {"source": "cat_application", "target": "inc_crash", "type": "contains", "weight": 2},
            {"source": "cat_application", "target": "inc_cpu", "type": "contains", "weight": 2},
            
            # Incidents to solutions
            {"source": "inc_conn_pool", "target": "sol_pool_size", "type": "resolves", "weight": 5},
            {"source": "inc_timeout", "target": "sol_index", "type": "resolves", "weight": 4},
            {"source": "inc_timeout", "target": "sol_cache", "type": "resolves", "weight": 3},
            {"source": "inc_deadlock", "target": "sol_index", "type": "resolves", "weight": 3},
            
            {"source": "inc_502", "target": "sol_restart", "type": "resolves", "weight": 4},
            {"source": "inc_502", "target": "sol_upgrade", "type": "resolves", "weight": 3},
            {"source": "inc_dns", "target": "sol_restart", "type": "resolves", "weight": 3},
            {"source": "inc_latency", "target": "sol_upgrade", "type": "resolves", "weight": 4},
            
            {"source": "inc_memory", "target": "sol_restart", "type": "resolves", "weight": 4},
            {"source": "inc_crash", "target": "sol_restart", "type": "resolves", "weight": 5},
            {"source": "inc_cpu", "target": "sol_cache", "type": "resolves", "weight": 3},
            
            # Incidents to systems
            {"source": "inc_conn_pool", "target": "sys_mysql", "type": "affects", "weight": 4},
            {"source": "inc_timeout", "target": "sys_mysql", "type": "affects", "weight": 3},
            {"source": "inc_502", "target": "sys_api", "type": "affects", "weight": 5},
            {"source": "inc_memory", "target": "sys_app", "type": "affects", "weight": 4},
            
            # Co-occurrence relationships
            {"source": "inc_conn_pool", "target": "inc_timeout", "type": "co-occurs", "weight": 2},
            {"source": "inc_502", "target": "inc_latency", "type": "co-occurs", "weight": 2},
            {"source": "inc_memory", "target": "inc_cpu", "type": "co-occurs", "weight": 3},
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "categories": 3,
                "incidents": 9,
                "solutions": 5,
                "systems": 3,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating graph data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns")
async def get_patterns():
    """Get common incident patterns and correlations"""
    try:
        patterns = [
            {
                "id": "pattern_1",
                "name": "Database Connection Storm",
                "incidents": ["Connection Pool Exhausted", "Query Timeout"],
                "frequency": 45,
                "avg_resolution_time": 25,
                "confidence": 0.89
            },
            {
                "id": "pattern_2",
                "name": "Network Cascade",
                "incidents": ["502 Bad Gateway", "DNS Resolution Failed", "High Latency"],
                "frequency": 32,
                "avg_resolution_time": 18,
                "confidence": 0.82
            },
            {
                "id": "pattern_3",
                "name": "Resource Exhaustion",
                "incidents": ["Memory Leak", "High CPU Usage"],
                "frequency": 28,
                "avg_resolution_time": 45,
                "confidence": 0.91
            }
        ]
        
        return {"patterns": patterns, "total": len(patterns)}
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/related/{incident_id}")
async def get_related_incidents(incident_id: str, depth: int = 2):
    """Get related incidents for a given incident"""
    try:
        # Mock related incidents
        related = {
            "incident_id": incident_id,
            "related_incidents": [
                {"id": "INC001", "title": "Database timeout", "similarity": 0.89},
                {"id": "INC002", "title": "Connection pool exhausted", "similarity": 0.76},
                {"id": "INC003", "title": "Query performance", "similarity": 0.68}
            ],
            "common_solutions": [
                {"solution": "Increase connection pool", "frequency": 12},
                {"solution": "Add database index", "frequency": 8}
            ],
            "depth": depth
        }
        
        return related
        
    except Exception as e:
        logger.error(f"Error getting related incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_graph():
    """Export graph data as JSON"""
    try:
        data = await get_graph_data()
        return {
            **data,
            "export_time": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
    except Exception as e:
        logger.error(f"Error exporting graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
