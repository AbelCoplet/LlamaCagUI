#!/usr/bin/env python3
"""
Token counter utility for LlamaCag UI

Provides token estimation functionality for documents.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Union, Optional, List, Dict

# Try to import tiktoken for better token estimation if available
try:
    import tiktoken
    HAVE_TIKTOKEN = True
except ImportError:
    HAVE_TIKTOKEN = False

# Supported file types and their average bytes per token
BYTES_PER_TOKEN = {
    'txt': 4.0,
    'md': 4.2,
    'html': 5.5,
    'pdf': 6.0,  # Higher because PDFs often have non-textual content
    'docx': 5.0,
    'default': 4.0  # Default if extension not recognized
}

def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in text"""
    if not text:
        return 0
    
    # If tiktoken is available, use it for better estimation
    if HAVE_TIKTOKEN:
        try:
            # Use cl100k_base encoding (used by many models including GPT-4)
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logging.warning(f"Error using tiktoken: {str(e)}")
            # Fall back to character-based estimation
    
    # Character-based estimation
    # This approach is rough but works for any text
    # Most modern tokenizers result in ~4 characters per token on average English text
    return len(text) // 4

def estimate_tokens_for_file(file_path: Union[str, Path]) -> int:
    """Estimate the number of tokens in a file"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Get file size
    file_size = file_path.stat().st_size
    
    # If file is very large, use size-based estimation first
    if file_size > 10 * 1024 * 1024:  # > 10MB
        return estimate_tokens_from_size(file_path)
    
    # For smaller files, try to read and estimate directly
    try:
        # Get file extension
        ext = file_path.suffix.lower().lstrip('.')
        
        # Handle different file types
        if ext in ['txt', 'md', 'html']:
            # Text files can be read directly
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            return estimate_tokens(text)
            
        elif ext == 'pdf':
            # Try to extract text from PDF
            try:
                import PyPDF2
                pdf_text = extract_text_from_pdf(file_path)
                if pdf_text:
                    return estimate_tokens(pdf_text)
            except ImportError:
                logging.warning("PyPDF2 not installed, falling back to size-based estimation for PDF")
            except Exception as e:
                logging.warning(f"Error extracting text from PDF: {str(e)}")
            
            # Fall back to size-based estimation
            return estimate_tokens_from_size(file_path)
            
        elif ext == 'docx':
            # Try to extract text from DOCX
            try:
                import docx
                doc_text = extract_text_from_docx(file_path)
                if doc_text:
                    return estimate_tokens(doc_text)
            except ImportError:
                logging.warning("python-docx not installed, falling back to size-based estimation for DOCX")
            except Exception as e:
                logging.warning(f"Error extracting text from DOCX: {str(e)}")
            
            # Fall back to size-based estimation
            return estimate_tokens_from_size(file_path)
            
        else:
            # Unsupported file type, use size-based estimation
            return estimate_tokens_from_size(file_path)
            
    except Exception as e:
        logging.error(f"Error estimating tokens for {file_path}: {str(e)}")
        # Fall back to size-based estimation
        return estimate_tokens_from_size(file_path)

def estimate_tokens_from_size(file_path: Path) -> int:
    """Estimate tokens based on file size and type"""
    file_size = file_path.stat().st_size
    ext = file_path.suffix.lower().lstrip('.')
    
    # Get bytes per token for this file type
    bytes_per_token = BYTES_PER_TOKEN.get(ext, BYTES_PER_TOKEN['default'])
    
    # Calculate token estimate
    return int(file_size / bytes_per_token)

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file"""
    try:
        import PyPDF2
        text = []
        
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page in pdf.pages:
                text.append(page.extract_text())
        
        return "\n\n".join(text)
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from a DOCX file"""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {str(e)}")
        return ""

def get_context_fit_status(token_count: int, context_size: int) -> Dict:
    """Check if tokens fit in context window and return status info"""
    # Calculate percentage of context used
    percentage = (token_count / context_size) * 100
    
    if token_count <= context_size * 0.9:  # Under 90%
        status = "fits"
        color = "#4CAF50"  # Green
        message = "Fits within context window"
    elif token_count <= context_size:  # Between 90% and 100%
        status = "tight"
        color = "#FFC107"  # Amber
        message = "Fits, but close to limit"
    elif token_count <= context_size * 1.2:  # Up to 20% over
        status = "over"
        color = "#FF9800"  # Orange
        message = "Slightly exceeds context window"
    else:  # More than 20% over
        status = "too_large"
        color = "#F44336"  # Red
        message = "Too large for context window"
    
    return {
        "status": status,
        "color": color,
        "message": message,
        "percentage": percentage,
        "fits": token_count <= context_size
    }
