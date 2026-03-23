"""
Mistral Embeddings Integration
Uses Mistral API for generating semantic embeddings (1536 dimensions)
"""

import os
import logging
from typing import List
from mistralai import Mistral

logger = logging.getLogger(__name__)


class MistralEmbeddingManager:
    """Manager for Mistral embeddings API calls"""
    
    # Mistral embedding model configuration
    MODEL = "mistral-embed"
    EMBEDDING_DIMENSION = 1536
    
    def __init__(self):
        """Initialize Mistral client with API key from environment"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        
        self.client = Mistral(api_key=api_key)
        logger.info(f"Initialized Mistral embeddings manager with model {self.MODEL}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text chunk
        
        Args:
            text: Text to embed (clause, document chunk, etc.)
            
        Returns:
            List[float]: 1536-dimensional embedding vector
            
        Raises:
            Exception: If API call fails
        """
        try:
            response = self.client.embeddings.create(
                model=self.MODEL,
                inputs=[text],
            )
            embedding = response.data[0].embedding
            
            if len(embedding) != self.EMBEDDING_DIMENSION:
                logger.warning(
                    f"Unexpected embedding dimension: {len(embedding)}, "
                    f"expected {self.EMBEDDING_DIMENSION}"
                )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call (more efficient)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            Exception: If API call fails
        """
        if not texts:
            return []
        
        try:
            response = self.client.embeddings.create(
                model=self.MODEL,
                inputs=texts,
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings successfully")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise


def get_mistral_embedder() -> MistralEmbeddingManager:
    """
    Get or create Mistral embeddings manager instance (lazy singleton)
    
    Returns:
        MistralEmbeddingManager: Initialized embeddings manager
    """
    if not hasattr(get_mistral_embedder, "_instance"):
        get_mistral_embedder._instance = MistralEmbeddingManager()
    
    return get_mistral_embedder._instance
