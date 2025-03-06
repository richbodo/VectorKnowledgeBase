import logging
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
            logger.info("Starting PDF text extraction...")
            logger.info(f"Input PDF size: {len(file_content)} bytes")

            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)

            logger.info(f"PDF loaded successfully. Number of pages: {len(pdf_reader.pages)}")

            text_content = []
            for i, page in enumerate(pdf_reader.pages):
                logger.info(f"Processing page {i+1}/{len(pdf_reader.pages)}...")
                try:
                    page_text = page.extract_text()
                    text_content.append(page_text)
                    logger.info(f"Extracted text from page {i+1}, length: {len(page_text)} chars")
                except Exception as page_error:
                    logger.error(f"Error extracting text from page {i+1}: {str(page_error)}", exc_info=True)
                    # Continue with next page instead of failing completely
                    text_content.append("")
                    continue

            full_text = "\n".join(text_content)
            if not full_text.strip():
                logger.warning("No text content found in PDF")
                return None, "No text content found in PDF"

            logger.info(f"Successfully extracted text, total length: {len(full_text)} chars")
            return full_text, None

        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return None, error_msg