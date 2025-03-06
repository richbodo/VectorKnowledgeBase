import logging
import os
import time
import traceback
from typing import List, Optional, Tuple
from openai import OpenAI
from config import OPENAI_API_KEY, EMBEDDING_MODEL
import httpx

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
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input="test"
            )
            logger.info("OpenAI API connection test successful")
            return True, None
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == 401:
                    error_msg = "Invalid API key or unauthorized access"
                elif e.response.status_code == 429:
                    error_msg = "API rate limit exceeded or quota exhausted"
            logger.error(f"OpenAI API connection test failed: {error_msg}")
            return False, error_msg

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

                except httpx.HTTPStatusError as http_error:
                    status_code = http_error.response.status_code
                    error_msg = http_error.response.text
                    logger.warning(
                        f"HTTP error on attempt {attempt + 1}: Status {status_code}\n"
                        f"Response: {error_msg}\n"
                        f"Headers: {dict(http_error.response.headers)}"
                    )

                    if status_code == 401:
                        raise ValueError("Invalid API key or unauthorized access") from http_error
                    elif status_code == 429:
                        error_msg = (
                            "OpenAI API rate limit exceeded or quota exhausted. "
                            "Please verify your API key and plan status."
                        )
                    elif status_code == 500:
                        error_msg = "OpenAI API server error. Please try again later."

                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise ValueError(error_msg) from http_error

                except Exception as api_error:
                    logger.warning(
                        f"API call attempt {attempt + 1} failed: {str(api_error)}\n"
                        f"{traceback.format_exc()}"
                    )
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating embedding: {error_msg}\n{traceback.format_exc()}")
            raise  # Re-raise the error to be handled by the caller