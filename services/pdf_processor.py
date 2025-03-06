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
            pdf_file = BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            
            text_content = []
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            full_text = "\n".join(text_content)
            if not full_text.strip():
                return None, "No text content found in PDF"
                
            return full_text, None
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return None, f"Error processing PDF: {str(e)}"
