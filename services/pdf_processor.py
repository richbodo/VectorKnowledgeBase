import logging
import time
from typing import Tuple, Optional
from PyPDF2 import PdfReader
from io import BytesIO

logger = logging.getLogger(__name__)

class PDFProcessor:
    @staticmethod
    def extract_text(file_content: bytes) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract text content from a PDF file
        Returns: Tuple[content, error_message]
        """
        try:
            start_time = time.time()
            logger.info("Starting PDF text extraction...")
            logger.info(f"Input PDF size: {len(file_content)} bytes")

            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF loaded successfully. Number of pages: {total_pages}")

            text_content = []
            chunk_size = 5  # Process 5 pages at a time

            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                logger.info(f"Processing chunk: pages {chunk_start + 1} to {chunk_end}")

                for i in range(chunk_start, chunk_end):
                    page_start_time = time.time()
                    logger.info(f"Starting page {i+1}/{total_pages}...")

                    try:
                        page = pdf_reader.pages[i]
                        logger.debug(f"Page {i+1} loaded into memory")

                        page_text = page.extract_text()
                        text_content.append(page_text)

                        page_time = time.time() - page_start_time
                        logger.info(f"Extracted text from page {i+1}, length: {len(page_text)} chars, took {page_time:.2f}s")

                    except Exception as page_error:
                        logger.error(f"Error extracting text from page {i+1}: {str(page_error)}", exc_info=True)
                        # Continue with next page instead of failing completely
                        text_content.append("")
                        continue

                # Free up memory after each chunk
                del page

            full_text = "\n".join(text_content)
            if not full_text.strip():
                logger.warning("No text content found in PDF")
                return None, "No text content found in PDF"

            total_time = time.time() - start_time
            logger.info(f"Successfully extracted text, total length: {len(full_text)} chars, took {total_time:.2f}s")
            return full_text, None

        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg