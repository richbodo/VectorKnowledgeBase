import logging
import openai
from typing import List, Optional
from config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        logger.info("Initializing EmbeddingService")
        if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith('sk-'):
            logger.error("Invalid or missing OPENAI_API_KEY")
            raise ValueError("OPENAI_API_KEY not configured correctly")

        openai.api_key = OPENAI_API_KEY
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        try:
            if not text.strip():
                logger.error("Empty text provided for embedding generation")
                return None

            logger.info(f"Generating embedding for text of length: {len(text)} chars")
            logger.debug(f"Text preview (first 100 chars): {text[:100]}...")

            response = openai.Embedding.create(
                model=EMBEDDING_MODEL,
                input=text
            )

            embedding = response['data'][0]['embedding']
            logger.info(f"Generated embedding vector of dimension {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise