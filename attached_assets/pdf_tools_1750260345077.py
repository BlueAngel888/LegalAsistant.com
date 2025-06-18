import fitz  # PyMuPDF

def extract_text_from_file(file_storage):
    doc = fitz.open(stream=file_storage.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text