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
            logger.debug(f"OpenAI API Key configured: {bool(openai.api_key)}")
            logger.debug(f"Using model: {EMBEDDING_MODEL}")

            logger.info("Making API call to OpenAI embeddings endpoint...")
            response = openai.embeddings.create(
                input=[text],  # Input must be a list of strings
                model=EMBEDDING_MODEL
            )
            logger.info("Successfully received response from OpenAI API")

            embedding = response.data[0].embedding
            logger.info(f"Generated embedding of dimension {len(embedding)}")
            return embedding

        except openai.APIError as api_error:
            logger.error(f"OpenAI API Error: {api_error}")
            logger.error(f"Error details: {str(api_error.__dict__)}")
            raise Exception(f"OpenAI API error: {str(api_error)}")
        except openai.APIConnectionError as conn_error:
            logger.error(f"Connection error with OpenAI API: {conn_error}")
            logger.error(f"Connection error details: {str(conn_error.__dict__)}")
            raise Exception(f"Connection error: {str(conn_error)}")
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            logger.error(f"Exception details: {str(e.__dict__)}")
            raise Exception(f"Unexpected error: {str(e)}")