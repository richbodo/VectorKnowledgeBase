import logging
import time
import traceback
import gc
import psutil
import os
import signal
from typing import Tuple, Optional
from PyPDF2 import PdfReader
from io import BytesIO
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds):
    def handler(signum, frame):
        raise TimeoutException("Operation timed out")

    # Register the signal function handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Disable the alarm
        signal.alarm(0)

class PDFProcessor:
    MAX_MEMORY_PER_PAGE = 200 * 1024 * 1024  # 200MB per page limit
    PAGE_TIMEOUT = 30  # 30 seconds timeout per page

    @staticmethod
    def check_memory():
        """Check current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss, memory_info.vms

    @staticmethod
    def log_memory_usage(operation: str = ""):
        """Log current memory usage"""
        rss, vms = PDFProcessor.check_memory()
        logger.info(f"Memory usage [{operation}] - RSS: {rss / 1024 / 1024:.2f}MB, VMS: {vms / 1024 / 1024:.2f}MB")

    @staticmethod
    def force_garbage_collection():
        """Force aggressive garbage collection"""
        gc.collect(generation=2)
        gc.collect(generation=1)
        gc.collect(generation=0)

    @staticmethod
    def extract_text(file_content: bytes) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract text content from a PDF file with memory management and timeouts
        Returns: Tuple[content, error_message]
        """
        try:
            start_time = time.time()
            logger.info("Starting PDF text extraction...")
            logger.info(f"Input PDF size: {len(file_content)} bytes")
            PDFProcessor.log_memory_usage("start")

            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF loaded successfully. Number of pages: {total_pages}")

            text_content = []

            for page_num in range(total_pages):
                chunk_start = time.time()
                logger.info(f"Starting page {page_num + 1}/{total_pages}...")
                PDFProcessor.log_memory_usage(f"before_page_{page_num + 1}")

                # Check memory limit before processing page
                rss, _ = PDFProcessor.check_memory()
                if rss > PDFProcessor.MAX_MEMORY_PER_PAGE:
                    logger.warning(f"Memory usage too high before processing page {page_num + 1}")
                    PDFProcessor.force_garbage_collection()
                    rss, _ = PDFProcessor.check_memory()
                    if rss > PDFProcessor.MAX_MEMORY_PER_PAGE:
                        error_msg = f"Memory limit exceeded ({rss / 1024 / 1024:.2f}MB)"
                        logger.error(error_msg)
                        return None, error_msg

                try:
                    # Load and process single page with timeout
                    with timeout(PDFProcessor.PAGE_TIMEOUT):
                        page = pdf_reader.pages[page_num]
                        logger.debug(f"Page {page_num + 1} loaded into memory")

                        # Extract text
                        page_text = page.extract_text()

                        if not page_text.strip():
                            logger.warning(f"Page {page_num + 1} appears to be empty or unreadable")
                            text_content.append("")
                        else:
                            text_content.append(page_text)
                            logger.info(f"Extracted text from page {page_num + 1}, length: {len(page_text)} chars")

                except TimeoutException:
                    logger.error(f"Timeout extracting text from page {page_num + 1}")
                    text_content.append("")
                    continue
                except Exception as page_error:
                    logger.error(f"Error extracting text from page {page_num + 1}: {str(page_error)}\n{traceback.format_exc()}")
                    text_content.append("")
                    continue
                finally:
                    # Explicit cleanup
                    if 'page' in locals():
                        del page
                    PDFProcessor.force_garbage_collection()
                    PDFProcessor.log_memory_usage(f"after_page_{page_num + 1}")

                chunk_time = time.time() - chunk_start
                logger.info(f"Page {page_num + 1} processing completed in {chunk_time:.2f}s")

            full_text = "\n".join(text_content)
            if not full_text.strip():
                logger.warning("No text content found in PDF")
                return None, "No text content found in PDF"

            total_time = time.time() - start_time
            logger.info(f"Successfully extracted text, total length: {len(full_text)} chars, took {total_time:.2f}s")
            PDFProcessor.log_memory_usage("end")
            return full_text, None

        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return None, error_msg