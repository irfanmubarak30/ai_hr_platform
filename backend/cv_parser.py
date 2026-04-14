import re
import io

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

def extract_text_from_pdf(file_bytes):
    """Extract text from PDF bytes using pdfplumber."""
    if not PDF_SUPPORT:
        return "PDF parsing not available. Please install pdfplumber."
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_email(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else ""

def extract_phone(text):
    pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
    matches = re.findall(pattern, text)
    return matches[0] if matches else ""

def extract_name(text):
    """Extract name from the top of a CV."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            if not any(kw in line.lower() for kw in ['email', 'phone', 'address', 'linkedin', 'objective']):
                return line
    return lines[0] if lines else "Unknown Candidate"

def parse_cv(file_bytes=None, text=None):
    """Parse CV from bytes or text and return structured data."""
    if file_bytes:
        text = extract_text_from_pdf(file_bytes)
    
    if not text:
        return {}

    name = extract_name(text)
    name_parts = name.split(' ', 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return {
        'first_name': first_name,
        'last_name': last_name,
        'full_name': name,
        'email': extract_email(text),
        'phone': extract_phone(text),
        'raw_text': text,
        'word_count': len(text.split())
    }
