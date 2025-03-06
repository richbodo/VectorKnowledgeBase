import logging
import os
from typing import List, Optional
import openai
from config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for input text"""
        try:
            if not text.strip():
                logger.error("Empty text provided for embedding generation")
                return None

            response = openai.Embedding.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None