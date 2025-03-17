import logging
import openai
import os
from typing import List, Optional
from config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        logger.info("Initializing EmbeddingService")
        
        # Import here to avoid circular imports
        from config import IS_DEPLOYMENT
        
        if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith('sk-'):
            logger.error("Invalid or missing OPENAI_API_KEY")
            if IS_DEPLOYMENT:
                logger.warning("Running in deployment mode with missing API key")
                self.api_available = False
            else:
                raise ValueError("OPENAI_API_KEY not configured correctly")
        else:
            self.api_available = True
            openai.api_key = OPENAI_API_KEY
            logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

    def generate_embedding(self, text: str):
        try:
            if not hasattr(self, 'api_available') or not self.api_available:
                logger.warning("Embedding API not available - returning dummy embedding")
                # Return a small dummy embedding in deployment mode
                return [0.0] * 10
                
            if not text.strip():
                logger.error("Empty text provided for embedding generation")
                return None

            # Privacy-enhanced logging - don't log text content
            text_length = len(text) if text else 0
            logger.info(f"Generating embedding for text of length: {text_length} chars")
            
            # No text preview to avoid logging content
            logger.debug("OpenAI API configuration status:")
            logger.debug(f"API Key configured: {bool(openai.api_key)}")
            logger.debug(f"Using model: {EMBEDDING_MODEL}")

            # Log API call without content details
            logger.info("Making API call to OpenAI embeddings endpoint...")
            
            # Use exception handling to prevent embedding content from appearing in error logs
            try:
                response = openai.embeddings.create(
                    input=[text],  # Input must be a list of strings
                    model=EMBEDDING_MODEL
                )
            except Exception as api_error:
                # Privacy-enhanced error handling - don't include text in error messages
                error_message = str(api_error)
                if text and len(text) > 10 and text[:10] in error_message:
                    sanitized_error = error_message.replace(text, "[TEXT CONTENT REDACTED]")
                    raise Exception(f"API error (sanitized): {sanitized_error}")
                raise
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