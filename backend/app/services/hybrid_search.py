"""
Hybrid Search Strategy
Combines semantic, keyword, and graph-based search with intelligent reranking
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
from datetime import datetime
from collections import Counter
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result"""
    id: str
    content: str
    score: float
    title: str = ""
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"  # semantic, keyword, graph, hybrid
    relevance_factors: Dict[str, float] = field(default_factory=dict)


class BM25Scorer:
    """
    BM25 (Best Matching 25) scoring for keyword search
    Industry-standard probabilistic relevance ranking
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1  # Term frequency saturation parameter
        self.b = b    # Length normalization parameter
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.num_docs: int = 0
        self.idf_scores: Dict[str, float] = {}

    def tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]  # Filter short tokens

    def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents for BM25 scoring"""
        self.num_docs = len(documents)

        # Calculate document frequencies and lengths
        all_terms = set()
        for doc in documents:
            doc_id = doc.get('id', '')
            content = doc.get('content', '')
            tokens = self.tokenize(content)

            self.doc_lengths[doc_id] = len(tokens)

            # Count term frequencies
            term_counts = Counter(tokens)
            for term in term_counts:
                all_terms.add(term)
                if term not in self.doc_freqs:
                    self.doc_freqs[term] = 0
                self.doc_freqs[term] += 1

        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.doc_lengths)

        # Calculate IDF scores
        for term in all_terms:
            df = self.doc_freqs.get(term, 0)
            idf = np.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
            self.idf_scores[term] = idf

        logger.info(f"BM25 indexed {self.num_docs} documents with {len(all_terms)} unique terms")

    def score(self, query: str, document: Dict[str, Any]) -> float:
        """Calculate BM25 score for a document given a query"""
        doc_id = document.get('id', '')
        content = document.get('content', '')

        query_tokens = self.tokenize(query)
        doc_tokens = self.tokenize(content)
        doc_term_counts = Counter(doc_tokens)

        doc_length = self.doc_lengths.get(doc_id, len(doc_tokens))

        score = 0.0
        for term in query_tokens:
            if term in doc_term_counts:
                tf = doc_term_counts[term]
                idf = self.idf_scores.get(term, 0.0)

                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_length / max(self.avg_doc_length, 1.0))
                )

                score += idf * (numerator / denominator)

        return score

    def search(self, query: str, documents: List[Dict[str, Any]], k: int = 5) -> List[SearchResult]:
        """Search documents using BM25"""
        if not documents:
            return []

        # Score all documents
        scored_docs = []
        for doc in documents:
            score = self.score(query, doc)
            if score > 0:
                result = SearchResult(
                    id=doc.get('id', ''),
                    content=doc.get('content', ''),
                    score=score,
                    title=doc.get('title', ''),
                    category=doc.get('category', ''),
                    metadata=doc.get('metadata', {}),
                    source="keyword_bm25",
                    relevance_factors={"bm25_score": score}
                )
                scored_docs.append(result)

        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x.score, reverse=True)
        return scored_docs[:k]


class HybridSearchEngine:
    """
    Hybrid search combining semantic, keyword, and optional graph-based search
    with intelligent fusion and reranking
    """

    def __init__(
        self,
        vector_store_service,
        config: Optional[Dict] = None
    ):
        self.vector_store = vector_store_service
        self.config = config or {}

        # Search weights for fusion
        self.semantic_weight = self.config.get('semantic_weight', 0.5)
        self.keyword_weight = self.config.get('keyword_weight', 0.3)
        self.graph_weight = self.config.get('graph_weight', 0.2)

        # BM25 scorer
        self.bm25 = BM25Scorer(
            k1=self.config.get('bm25_k1', 1.5),
            b=self.config.get('bm25_b', 0.75)
        )

        # Document cache for BM25
        self.indexed_documents: List[Dict[str, Any]] = []
        self.index_initialized = False

        logger.info("Hybrid Search Engine initialized")

    async def initialize_index(self, documents: List[Dict[str, Any]]):
        """Initialize BM25 index with documents"""
        self.indexed_documents = documents
        self.bm25.index_documents(documents)
        self.index_initialized = True
        logger.info(f"Hybrid search index initialized with {len(documents)} documents")

    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        enable_rerank: bool = True
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining multiple strategies

        Args:
            query: Search query
            k: Number of results to return
            enable_rerank: Whether to apply reranking

        Returns:
            List of unified search results
        """
        logger.info(f"Hybrid search for: '{query}' (k={k})")

        # Run all search strategies in parallel
        semantic_task = self._semantic_search(query, k * 2)
        keyword_task = self._keyword_search(query, k * 2)

        # Wait for both to complete
        semantic_results, keyword_results = await asyncio.gather(
            semantic_task,
            keyword_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(semantic_results, Exception):
            logger.error(f"Semantic search failed: {semantic_results}")
            semantic_results = []

        if isinstance(keyword_results, Exception):
            logger.error(f"Keyword search failed: {keyword_results}")
            keyword_results = []

        # Fuse results
        fused_results = self._fuse_results(
            semantic_results,
            keyword_results,
            []  # graph_results placeholder
        )

        # Rerank if enabled
        if enable_rerank and fused_results:
            fused_results = await self._rerank_results(query, fused_results)

        # Return top k
        final_results = fused_results[:k]

        logger.info(
            f"Hybrid search complete: {len(final_results)} results "
            f"(semantic: {len(semantic_results)}, keyword: {len(keyword_results)})"
        )

        return final_results

    async def _semantic_search(self, query: str, k: int) -> List[SearchResult]:
        """Semantic similarity search using vector embeddings"""
        try:
            vector_results = await self.vector_store.similarity_search(query, k)

            results = []
            for doc in vector_results:
                result = SearchResult(
                    id=doc.get('id', ''),
                    content=doc.get('content', ''),
                    score=doc.get('score', 0.0),
                    title=doc.get('title', ''),
                    category=doc.get('category', ''),
                    metadata=doc.get('metadata', {}),
                    source="semantic",
                    relevance_factors={"semantic_score": doc.get('score', 0.0)}
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def _keyword_search(self, query: str, k: int) -> List[SearchResult]:
        """Keyword-based search using BM25"""
        try:
            if not self.index_initialized:
                # Try to initialize with available documents
                logger.warning("BM25 index not initialized, using empty index")
                return []

            results = self.bm25.search(query, self.indexed_documents, k)
            return results

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _fuse_results(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        graph_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Fuse results from multiple search strategies using weighted combination

        Uses Reciprocal Rank Fusion (RRF) combined with score-based weighting
        """
        # Combine all results
        all_results: Dict[str, SearchResult] = {}

        # Process semantic results
        for rank, result in enumerate(semantic_results, 1):
            doc_id = result.id
            rrf_score = 1.0 / (60 + rank)  # RRF with k=60

            if doc_id not in all_results:
                all_results[doc_id] = result
                all_results[doc_id].relevance_factors = {}

            all_results[doc_id].relevance_factors['semantic_rrf'] = rrf_score
            all_results[doc_id].relevance_factors['semantic_score'] = result.score

        # Process keyword results
        for rank, result in enumerate(keyword_results, 1):
            doc_id = result.id
            rrf_score = 1.0 / (60 + rank)

            if doc_id not in all_results:
                all_results[doc_id] = result
                all_results[doc_id].relevance_factors = {}

            all_results[doc_id].relevance_factors['keyword_rrf'] = rrf_score
            all_results[doc_id].relevance_factors['keyword_score'] = result.score

        # Calculate final fusion scores
        for doc_id, result in all_results.items():
            factors = result.relevance_factors

            # Weighted combination of RRF scores
            fusion_score = (
                self.semantic_weight * factors.get('semantic_rrf', 0.0) +
                self.keyword_weight * factors.get('keyword_rrf', 0.0) +
                self.graph_weight * factors.get('graph_rrf', 0.0)
            )

            # Bonus for appearing in multiple result sets
            appearance_count = sum([
                1 if 'semantic_rrf' in factors else 0,
                1 if 'keyword_rrf' in factors else 0,
                1 if 'graph_rrf' in factors else 0
            ])

            if appearance_count > 1:
                fusion_score *= (1.0 + 0.2 * appearance_count)  # 20% bonus per additional source

            result.score = fusion_score
            result.source = "hybrid"

        # Sort by fusion score
        fused_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)

        return fused_results

    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Rerank results using advanced scoring

        Considers:
        - Query-document relevance
        - Document quality signals
        - Recency (if available)
        - Category matching
        """
        query_lower = query.lower()
        query_terms = set(self.bm25.tokenize(query))

        for result in results:
            rerank_factors = {}

            # 1. Title matching bonus
            title_lower = result.title.lower()
            if any(term in title_lower for term in query_terms):
                rerank_factors['title_match'] = 0.2
            else:
                rerank_factors['title_match'] = 0.0

            # 2. Exact phrase matching
            if query_lower in result.content.lower():
                rerank_factors['exact_match'] = 0.3
            else:
                rerank_factors['exact_match'] = 0.0

            # 3. Content length penalty (prefer concise, relevant content)
            content_length = len(result.content)
            if content_length < 500:
                rerank_factors['length_factor'] = 0.1
            elif content_length > 2000:
                rerank_factors['length_factor'] = -0.1
            else:
                rerank_factors['length_factor'] = 0.0

            # 4. Recency bonus (if timestamp available)
            if 'timestamp' in result.metadata:
                try:
                    doc_time = datetime.fromisoformat(result.metadata['timestamp'])
                    age_days = (datetime.now() - doc_time).days
                    if age_days < 30:
                        rerank_factors['recency'] = 0.15
                    elif age_days < 90:
                        rerank_factors['recency'] = 0.05
                    else:
                        rerank_factors['recency'] = 0.0
                except:
                    rerank_factors['recency'] = 0.0
            else:
                rerank_factors['recency'] = 0.0

            # Calculate rerank adjustment
            rerank_adjustment = sum(rerank_factors.values())

            # Apply adjustment (cap between -0.3 and +0.5)
            rerank_adjustment = max(-0.3, min(0.5, rerank_adjustment))

            # Update score
            original_score = result.score
            result.score = original_score * (1.0 + rerank_adjustment)

            # Store rerank factors in metadata
            result.relevance_factors['rerank_adjustment'] = rerank_adjustment
            result.relevance_factors['rerank_factors'] = rerank_factors

        # Re-sort after reranking
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get hybrid search statistics"""
        return {
            "index_initialized": self.index_initialized,
            "indexed_documents": len(self.indexed_documents),
            "bm25_unique_terms": len(self.bm25.idf_scores),
            "configuration": {
                "semantic_weight": self.semantic_weight,
                "keyword_weight": self.keyword_weight,
                "graph_weight": self.graph_weight,
                "bm25_k1": self.bm25.k1,
                "bm25_b": self.bm25.b
            }
        }


class QueryExpander:
    """
    Query expansion for improved retrieval
    Adds synonyms and related terms to queries
    """

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

        # Simple synonym dictionary for common IT terms
        self.synonyms = {
            "down": ["offline", "unavailable", "not responding"],
            "slow": ["performance issue", "latency", "delay"],
            "error": ["exception", "failure", "problem"],
            "crash": ["failure", "terminated", "stopped"],
            "timeout": ["unresponsive", "hanging", "delay"],
            "memory": ["ram", "heap", "memory leak"],
            "cpu": ["processor", "computing", "performance"],
            "database": ["db", "sql", "datastore"],
            "api": ["endpoint", "service", "interface"],
            "connection": ["connectivity", "network", "link"]
        }

    async def expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expansions = [query]  # Include original query

        # Simple keyword expansion
        query_lower = query.lower()
        for term, synonyms in self.synonyms.items():
            if term in query_lower:
                for synonym in synonyms[:2]:  # Limit to 2 synonyms
                    expanded = query_lower.replace(term, synonym)
                    if expanded != query_lower:
                        expansions.append(expanded)

        # If LLM available, use it for more sophisticated expansion
        if self.llm_service:
            try:
                llm_expansion = await self._llm_expand(query)
                if llm_expansion:
                    expansions.extend(llm_expansion[:2])  # Add top 2 LLM expansions
            except Exception as e:
                logger.warning(f"LLM query expansion failed: {e}")

        return expansions[:5]  # Return max 5 query variations

    async def _llm_expand(self, query: str) -> List[str]:
        """Use LLM to expand query"""
        prompt = f"""
        Generate 2 alternative phrasings of this query that preserve the intent:

        Query: {query}

        Alternatives (one per line):
        """

        result = await self.llm_service.generate(
            prompt=prompt,
            max_tokens=100,
            temperature=0.7
        )

        alternatives = [line.strip() for line in result.split('\n') if line.strip()]
        return alternatives[:2]
