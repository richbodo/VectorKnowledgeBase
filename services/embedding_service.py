import logging
import openai
import os
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

    def generate_embedding(self, text: str):
        try:
            if not text.strip():
                logger.error("Empty text provided for embedding generation")
                return None

            logger.info(f"Generating embedding for text of length: {len(text)} chars")
            logger.debug(f"Text preview (first 100 chars): {text[:100]}...")

            response = openai.embeddings.create(
                input=[text],  # Input must be a list of strings
                model=EMBEDDING_MODEL
            )
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding of dimension {len(embedding)}")
            return embedding

        except openai.APIError as api_error:
            logger.error(f"OpenAI API Error: {api_error}")
            raise Exception(f"OpenAI API error: {str(api_error)}")
        except openai.APIConnectionError as conn_error:
            logger.error(f"Connection error with OpenAI API: {conn_error}")
            raise Exception(f"Connection error: {str(conn_error)}")
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")