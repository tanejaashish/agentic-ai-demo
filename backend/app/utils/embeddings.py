"""
Embeddings generation utility
"""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """
    Generate embeddings for text using sentence transformers
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model {self.model_name} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            # Fallback to random embeddings for demo
            self.model = None
    
    def generate(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model is not None:
            try:
                embeddings = self.model.encode(
                    texts,
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )
                return embeddings
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
        
        # Fallback to random embeddings for demo
        return self._generate_random_embeddings(texts, normalize)
    
    def _generate_random_embeddings(
        self,
        texts: List[str],
        normalize: bool = True
    ) -> np.ndarray:
        """
        Generate random embeddings as fallback
        """
        # Use text length as seed for consistency
        embeddings = []
        
        for text in texts:
            # Generate deterministic "random" embedding based on text
            seed = sum(ord(c) for c in text[:100])  # Use first 100 chars
            np.random.seed(seed)
            embedding = np.random.randn(384)  # 384 dimensions for MiniLM
            
            if normalize:
                # L2 normalization
                embedding = embedding / np.linalg.norm(embedding)
            
            embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings
        """
        if self.model is not None:
            return self.model.get_sentence_embedding_dimension()
        return 384  # Default for MiniLM
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        """
        # Ensure 1D arrays
        if embedding1.ndim > 1:
            embedding1 = embedding1.flatten()
        if embedding2.ndim > 1:
            embedding2 = embedding2.flatten()
        
        # Compute cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def batch_compute_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute similarity between query and multiple embeddings
        """
        if query_embedding.ndim > 1:
            query_embedding = query_embedding.flatten()
        
        # Normalize query
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings_norm = embeddings / norms
        
        # Compute similarities
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities