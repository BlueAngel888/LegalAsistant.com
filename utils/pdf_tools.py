import os
import logging
from werkzeug.datastructures import FileStorage
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from docx import Document

def extract_text_from_file(file_storage: FileStorage) -> str:
    """
    Extract text from various file formats including PDF, DOCX, DOC, and images.
    """
    try:
        filename = file_storage.filename.lower()
        file_content = file_storage.read()
        
        if filename.endswith('.pdf'):
            return extract_text_from_pdf(file_content)
        elif filename.endswith(('.docx', '.doc')):
            return extract_text_from_docx(file_content)
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            return extract_text_from_image(file_content)
        elif filename.endswith('.txt'):
            return file_content.decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file format: {filename}")
            
    except Exception as e:
        logging.error(f"Error extracting text from file {file_storage.filename}: {str(e)}")
        raise

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF content."""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()
            
            # If no text found, try OCR on the page
            if not page_text.strip():
                try:
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    page_text = extract_text_from_image(img_data)
                except Exception as ocr_error:
                    logging.warning(f"OCR failed for page {page_num + 1}: {str(ocr_error)}")
            
            text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
        
        doc.close()
        return text
        
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        raise

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
