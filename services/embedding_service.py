import logging
import os
import time
import traceback
from typing import List, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        logger.info("Initializing EmbeddingService")
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for input text"""
        try:
            start_time = time.time()

            if not text.strip():
                logger.error("Empty text provided for embedding generation")
                return None

            logger.info(f"Generating embedding for text of length: {len(text)} chars")
            logger.debug(f"Text preview (first 100 chars): {text[:100]}...")

            # Add retries for API call
            max_retries = 3
            retry_delay = 1  # seconds

            for attempt in range(max_retries):
                try:
                    api_start = time.time()
                    logger.debug(f"Making API call attempt {attempt + 1}")

                    response = self.client.embeddings.create(
                        model=EMBEDDING_MODEL,
                        input=text
                    )
                    api_time = time.time() - api_start
                    logger.info(f"OpenAI API call completed in {api_time:.2f}s")

                    # Debug log the response structure
                    logger.debug(f"API Response structure: {response}")

                    embedding = response.data[0].embedding
                    total_time = time.time() - start_time
                    logger.info(f"Successfully generated embedding vector of dimension {len(embedding)} in {total_time:.2f}s")
                    return embedding

                except Exception as api_error:
                    logger.warning(f"API call attempt {attempt + 1} failed: {str(api_error)}\n{traceback.format_exc()}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise  # Re-raise the last error if all retries failed

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}\n{traceback.format_exc()}")
            return None