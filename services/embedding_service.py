import logging
import os
import time
import traceback
from typing import List, Optional, Tuple
from openai import OpenAI
from config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        """Initialize the OpenAI client with proper error handling"""
        logger.info("Initializing EmbeddingService")
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY not configured")

        # Validate API key format
        if not OPENAI_API_KEY.startswith('sk-'):
            logger.error("Invalid API key format: key must start with 'sk-'")
            raise ValueError("Invalid OpenAI API key format")

        # Log key presence (not the actual key)
        logger.info("OpenAI API key found, validating format...")
        logger.debug(f"API key format validation: starts with 'sk-': {OPENAI_API_KEY.startswith('sk-')}, length: {len(OPENAI_API_KEY)}")

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test the OpenAI API connection"""
        try:
            # Make a minimal API call to test the connection
            test_text = "test"
            logger.info(f"Testing API connection with text: {test_text}")

            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=test_text
            )

            # Verify we got a valid response
            if hasattr(response, 'data') and len(response.data) > 0:
                logger.info("OpenAI API connection test successful")
                return True, None
            else:
                error_msg = "API response missing embedding data"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI API connection test failed: {error_msg}")
            return False, error_msg

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for input text"""
        try:
            if not text.strip():
                logger.error("Empty text provided for embedding generation")
                return None

            logger.info(f"Generating embedding for text of length: {len(text)} chars")
            logger.debug(f"Text preview (first 100 chars): {text[:100]}...")

            # Simple direct API call without retries
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )

            # Extract embedding from response
            embedding = response.data[0].embedding
            logger.info(f"Successfully generated embedding vector of dimension {len(embedding)}")
            return embedding

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating embedding: {error_msg}\n{traceback.format_exc()}")
            raise  # Re-raise the error to be handled by the caller