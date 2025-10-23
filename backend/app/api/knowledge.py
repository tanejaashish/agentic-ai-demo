"""
API routes for knowledge base management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.incident import Category

router = APIRouter()

# In-memory knowledge base for demo
knowledge_articles = [
    {
        "id": "KB001",
        "title": "Database Connection Pool Best Practices",
        "category": "Database",
        "content": "Configure connection pools with appropriate sizing...",
        "tags": ["database", "performance", "connection"],
        "usage_count": 45,
        "effectiveness_score": 0.88
    },
    {
        "id": "KB002",
        "title": "API Gateway Troubleshooting Guide",
        "category": "Network",
        "content": "Common API gateway issues and solutions...",
        "tags": ["api", "gateway", "network"],
        "usage_count": 32,
        "effectiveness_score": 0.85
    }
]

@router.get("/articles", response_model=List[Dict[str, Any]])
async def list_knowledge_articles(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    tag: Optional[str] = None
):
    """
    List knowledge base articles with optional filtering
    """
    filtered = knowledge_articles
    
    if category:
        filtered = [a for a in filtered if a.get("category") == category]
    
    if tag:
        filtered = [a for a in filtered if tag in a.get("tags", [])]
    
    return filtered[offset:offset + limit]

@router.get("/articles/{article_id}")
async def get_knowledge_article(article_id: str):
    """
    Get a specific knowledge article
    """
    for article in knowledge_articles:
        if article["id"] == article_id:
            # Increment usage count
            article["usage_count"] += 1
            return article
    
    raise HTTPException(status_code=404, detail="Article not found")

@router.post("/articles")
async def create_knowledge_article(article: Dict[str, Any]):
    """
    Create a new knowledge article
    """
    # Generate ID
    article_id = f"KB{len(knowledge_articles) + 1:03d}"
    
    new_article = {
        "id": article_id,
        "title": article.get("title"),
        "category": article.get("category"),
        "content": article.get("content"),
        "tags": article.get("tags", []),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "usage_count": 0,
        "effectiveness_score": None
    }
    
    knowledge_articles.append(new_article)
    
    return {
        "status": "success",
        "article_id": article_id,
        "message": "Knowledge article created successfully"
    }

@router.put("/articles/{article_id}")
async def update_knowledge_article(
    article_id: str,
    article: Dict[str, Any]
):
    """
    Update an existing knowledge article
    """
    for i, existing in enumerate(knowledge_articles):
        if existing["id"] == article_id:
            # Update fields
            existing.update(article)
            existing["updated_at"] = datetime.utcnow().isoformat()
            knowledge_articles[i] = existing
            
            return {
                "status": "success",
                "message": "Article updated successfully"
            }
    
    raise HTTPException(status_code=404, detail="Article not found")

@router.delete("/articles/{article_id}")
async def delete_knowledge_article(article_id: str):
    """
    Delete a knowledge article
    """
    global knowledge_articles
    original_count = len(knowledge_articles)
    knowledge_articles = [a for a in knowledge_articles if a["id"] != article_id]
    
    if len(knowledge_articles) < original_count:
        return {
            "status": "success",
            "message": "Article deleted successfully"
        }
    
    raise HTTPException(status_code=404, detail="Article not found")

@router.get("/search")
async def search_knowledge_base(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search knowledge base using natural language
    """
    results = []
    query_lower = query.lower()
    
    for article in knowledge_articles:
        # Simple text matching for demo
        if (query_lower in article["title"].lower() or
            query_lower in article["content"].lower() or
            any(query_lower in tag for tag in article.get("tags", []))):
            
            results.append({
                **article,
                "relevance_score": 0.75  # Simulated relevance
            })
            
            if len(results) >= limit:
                break
    
    return {
        "query": query,
        "results": results,
        "total_found": len(results)
    }

@router.get("/stats")
async def get_knowledge_base_stats():
    """
    Get knowledge base statistics
    """
    total_articles = len(knowledge_articles)
    
    if total_articles == 0:
        return {
            "total_articles": 0,
            "categories": {},
            "most_used": [],
            "most_effective": []
        }
    
    # Calculate statistics
    categories = {}
    for article in knowledge_articles:
        cat = article.get("category", "uncategorized")
        categories[cat] = categories.get(cat, 0) + 1
    
    # Sort by usage
    most_used = sorted(
        knowledge_articles,
        key=lambda x: x.get("usage_count", 0),
        reverse=True
    )[:5]
    
    # Sort by effectiveness
    articles_with_scores = [
        a for a in knowledge_articles 
        if a.get("effectiveness_score") is not None
    ]
    most_effective = sorted(
        articles_with_scores,
        key=lambda x: x.get("effectiveness_score", 0),
        reverse=True
    )[:5]
    
    return {
        "total_articles": total_articles,
        "categories": categories,
        "most_used": [
            {"id": a["id"], "title": a["title"], "usage_count": a["usage_count"]}
            for a in most_used
        ],
        "most_effective": [
            {"id": a["id"], "title": a["title"], "score": a["effectiveness_score"]}
            for a in most_effective
        ],
        "average_usage": sum(a.get("usage_count", 0) for a in knowledge_articles) / total_articles
    }

@router.post("/sync")
async def sync_knowledge_base():
    """
    Sync knowledge base with vector store
    """
    # This would trigger actual sync in production
    return {
        "status": "success",
        "message": "Knowledge base sync initiated",
        "articles_synced": len(knowledge_articles),
        "timestamp": datetime.utcnow().isoformat()
    }