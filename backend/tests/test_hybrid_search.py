"""
Tests for Hybrid Search Engine
"""

import pytest
from app.services.hybrid_search import (
    HybridSearchEngine,
    BM25Scorer,
    SearchResult
)


@pytest.mark.unit
class TestBM25Scorer:
    """Test BM25 scoring algorithm"""

    def test_bm25_initialization(self):
        """Test BM25 scorer initialization"""
        scorer = BM25Scorer(k1=1.5, b=0.75)
        assert scorer.k1 == 1.5
        assert scorer.b == 0.75

    def test_bm25_tokenization(self):
        """Test text tokenization"""
        scorer = BM25Scorer()
        tokens = scorer.tokenize("Database connection timeout error")
        assert "database" in tokens
        assert "connection" in tokens
        assert "timeout" in tokens

    def test_bm25_indexing(self, sample_documents):
        """Test document indexing"""
        scorer = BM25Scorer()
        scorer.index_documents(sample_documents)

        assert scorer.num_docs == len(sample_documents)
        assert len(scorer.doc_lengths) == len(sample_documents)
        assert len(scorer.idf_scores) > 0

    def test_bm25_search(self, sample_documents):
        """Test BM25 search"""
        scorer = BM25Scorer()
        scorer.index_documents(sample_documents)

        results = scorer.search("database timeout", sample_documents, k=2)

        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.score > 0 for r in results)


@pytest.mark.integration
class TestHybridSearchEngine:
    """Test Hybrid Search Engine"""

    @pytest.mark.asyncio
    async def test_hybrid_search_initialization(self):
        """Test hybrid search initialization"""
        # Mock vector store
        class MockVectorStore:
            async def similarity_search(self, query, k):
                return []

        engine = HybridSearchEngine(
            vector_store_service=MockVectorStore(),
            config={
                'semantic_weight': 0.5,
                'keyword_weight': 0.3
            }
        )

        assert engine.semantic_weight == 0.5
        assert engine.keyword_weight == 0.3

    @pytest.mark.asyncio
    async def test_index_initialization(self, sample_documents):
        """Test search index initialization"""
        class MockVectorStore:
            async def similarity_search(self, query, k):
                return []

        engine = HybridSearchEngine(vector_store_service=MockVectorStore())
        await engine.initialize_index(sample_documents)

        assert engine.index_initialized
        assert len(engine.indexed_documents) == len(sample_documents)

    @pytest.mark.asyncio
    async def test_result_fusion(self, sample_documents):
        """Test result fusion from multiple sources"""
        class MockVectorStore:
            async def similarity_search(self, query, k):
                return [
                    {
                        'id': 'doc-001',
                        'content': 'test',
                        'score': 0.9,
                        'title': 'Test',
                        'category': 'test',
                        'metadata': {}
                    }
                ]

        engine = HybridSearchEngine(vector_store_service=MockVectorStore())
        await engine.initialize_index(sample_documents)

        results = await engine.hybrid_search("database timeout", k=3)

        assert isinstance(results, list)
        assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_reranking(self, sample_documents):
        """Test result reranking"""
        class MockVectorStore:
            async def similarity_search(self, query, k):
                return []

        engine = HybridSearchEngine(vector_store_service=MockVectorStore())
        await engine.initialize_index(sample_documents)

        # Create sample results
        results = [
            SearchResult(
                id="doc-001",
                content="database connection timeout",
                score=0.8,
                title="Test",
                category="database",
                source="test"
            )
        ]

        reranked = await engine._rerank_results("database timeout", results)

        assert len(reranked) == len(results)
        assert all(hasattr(r, 'relevance_factors') for r in reranked)
