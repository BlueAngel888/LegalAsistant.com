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
                
                # A scanned page needs real OCR; never represent a placeholder as
                # extracted legal text.
                if not page_text or not page_text.strip():
                    logging.warning(f"No text found on page {page_num + 1}, OCR might be needed")
                    continue
                
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
            except Exception as page_error:
                logging.warning(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
                continue
        
        if not text.strip():
            raise ValueError("No text could be extracted from this PDF")
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
    """Extract text from image using OCR with optimizations."""
    try:
        image = Image.open(io.BytesIO(file_content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Optimize image size for faster OCR processing
        # Reduce size if image is very large
        max_dimension = 2000
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int((height * max_dimension) / width)
            else:
                new_height = max_dimension
                new_width = int((width * max_dimension) / height)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logging.info(f"Resized image from {width}x{height} to {new_width}x{new_height} for faster processing")
        
        # Use fast OCR configuration with timeout protection
        custom_config = r'--oem 3 --psm 6'
        
        # Set timeout for OCR processing (max 10 seconds per image)
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("OCR processing timeout")
        
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)  # 10 second timeout
            text = pytesseract.image_to_string(image, lang='eng', config=custom_config)
            signal.alarm(0)  # Cancel alarm
        except TimeoutError:
            signal.alarm(0)
            logging.warning("OCR timeout - using fallback processing")
            # Try simpler/faster config
            text = pytesseract.image_to_string(image, lang='eng', config='--psm 8')
        except Exception as ocr_error:
            signal.alarm(0)
            logging.error(f"OCR error: {str(ocr_error)}")
            text = ""
        
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
