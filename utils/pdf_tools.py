import os
import logging
from werkzeug.datastructures import FileStorage
from PIL import Image
import pytesseract
import io
from docx import Document

# Import PyPDF2 for PDF processing
import PyPDF2

def extract_text_from_file(file_storage: FileStorage) -> str:
    """
    Extract text from various file formats including PDF, DOCX, DOC, and images.
    """
    try:
        filename = file_storage.filename
        if not filename:
            raise ValueError("No filename provided")
            
        filename_lower = filename.lower()
        file_content = file_storage.read()
        
        if filename_lower.endswith('.pdf'):
            return extract_text_from_pdf(file_content)
        elif filename_lower.endswith(('.docx', '.doc')):
            return extract_text_from_docx(file_content)
        elif filename_lower.endswith(('.jpg', '.jpeg', '.png')):
            return extract_text_from_image(file_content)
        elif filename_lower.endswith('.txt'):
            return file_content.decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file format: {filename}")
            
    except Exception as e:
        logging.error(f"Error extracting text from file {file_storage.filename}: {str(e)}")
        raise

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF content using PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                
                # If no text found, try OCR on the page (would need pdf2image for this)
                if not page_text.strip():
                    logging.warning(f"No text found on page {page_num + 1}, OCR might be needed")
                    page_text = f"[Page {page_num + 1} appears to be an image or has no extractable text]"
                
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
            except Exception as page_error:
                logging.warning(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
                text += f"\n--- Page {page_num + 1} ---\n[Error extracting text from this page]\n"
        
        return text if text.strip() else "No text could be extracted from this PDF."
        
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return f"Error processing PDF: {str(e)}. Please try converting to DOCX or image format."

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX content."""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        
        return text
        
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {str(e)}")
        raise

def extract_text_from_image(file_content: bytes) -> str:
    """Extract text from image using OCR."""
    try:
        image = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use Tesseract OCR to extract text
        text = pytesseract.image_to_string(image, lang='eng')
        
        return text
        
    except Exception as e:
        logging.error(f"Error extracting text from image: {str(e)}")
        # If OCR fails, return empty string rather than raising exception
        return ""

def get_file_info(file_storage: FileStorage) -> dict:
    """Get basic information about the uploaded file."""
    return {
        'filename': file_storage.filename,
        'content_type': file_storage.content_type,
        'size': len(file_storage.read())
    }
