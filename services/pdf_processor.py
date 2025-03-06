import logging
import time
import traceback
import gc
import psutil
import os
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
            chunk_size = 1  # Process one page at a time

            def log_memory_usage():
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                logger.info(f"Memory usage - RSS: {memory_info.rss / 1024 / 1024:.2f}MB, VMS: {memory_info.vms / 1024 / 1024:.2f}MB")

            for page_num in range(total_pages):
                chunk_start = time.time()
                logger.info(f"Starting page {page_num + 1}/{total_pages}...")
                log_memory_usage()

                try:
                    # Load and process single page
                    page = pdf_reader.pages[page_num]
                    logger.debug(f"Page {page_num + 1} loaded into memory")

                    # Extract text with timeout protection
                    page_text = page.extract_text()

                    if not page_text.strip():
                        logger.warning(f"Page {page_num + 1} appears to be empty or unreadable")
                        text_content.append("")
                    else:
                        text_content.append(page_text)
                        logger.info(f"Extracted text from page {page_num + 1}, length: {len(page_text)} chars")

                except Exception as page_error:
                    logger.error(f"Error extracting text from page {page_num + 1}: {str(page_error)}\n{traceback.format_exc()}")
                    # Continue with next page instead of failing completely
                    text_content.append("")
                    continue

                finally:
                    # Explicit cleanup
                    if 'page' in locals():
                        del page
                    gc.collect()
                    log_memory_usage()

                chunk_time = time.time() - chunk_start
                logger.info(f"Page {page_num + 1} processing completed in {chunk_time:.2f}s")

                # Force garbage collection between pages
                gc.collect()
                gc.collect()  # Double collection to ensure cleanup of circular references

            full_text = "\n".join(text_content)
            if not full_text.strip():
                logger.warning("No text content found in PDF")
                return None, "No text content found in PDF"

            total_time = time.time() - start_time
            logger.info(f"Successfully extracted text, total length: {len(full_text)} chars, took {total_time:.2f}s")
            return full_text, None

        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return None, error_msg