"""
PactLens Backend - Utilities for PDF Processing
Extract text and metadata from PDF documents
"""

import PyPDF2
import os
from typing import Tuple, List
from pathlib import Path


class PDFProcessor:
    """Process and extract text from PDF files"""
    
    @staticmethod
    def extract_text_and_metadata(file_path: str) -> Tuple[str, dict]:
        """
        Extract full text and metadata from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (full_text, metadata)
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Extract text from all pages
                full_text = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    full_text += f"\n--- Page {page_num + 1} ---\n"
                    full_text += page.extract_text()
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                metadata = {
                    "pages": num_pages,
                    "size": file_size,
                    "filename": Path(file_path).name,
                }
                
                return full_text, metadata
        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")
    
    @staticmethod
    def chunk_by_sections(text: str, min_section_length: int = 100) -> List[dict]:
        """
        Intelligently chunk text by sections/clauses
        Looks for common legal section patterns
        
        Args:
            text: Full document text
            min_section_length: Minimum characters per chunk
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        current_chunk = ""
        current_section = ""
        current_number = ""
        start_page = 1
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Detect page markers
            if '--- Page' in line:
                try:
                    page_num = int(line.split('Page ')[1].split(' ---')[0])
                    start_page = page_num
                except:
                    pass
                continue
            
            # Detect section headers (e.g., "1. Confidentiality", "2.1 Definition")
            stripped = line.strip()
            if self._is_section_header(stripped):
                # Save previous chunk
                if current_chunk.strip() and len(current_chunk.strip()) > min_section_length:
                    chunks.append({
                        "section": current_number,
                        "title": current_section,
                        "text": current_chunk.strip(),
                        "start_page": start_page,
                    })
                
                # Start new section
                current_section, current_number = self._parse_section_header(stripped)
                current_chunk = ""
            else:
                current_chunk += line + "\n"
        
        # Save final chunk
        if current_chunk.strip() and len(current_chunk.strip()) > min_section_length:
            chunks.append({
                "section": current_number,
                "title": current_section,
                "text": current_chunk.strip(),
                "start_page": start_page,
            })
        
        return chunks if chunks else self._fallback_chunking(text)
    
    @staticmethod
    def _is_section_header(line: str) -> bool:
        """Check if a line is a section header"""
        if len(line) < 3 or len(line) > 200:
            return False
        
        # Pattern: starts with number(s) followed by period or dot
        import re
        return bool(re.match(r'^(\d+(\.\d+)*[\.\)]?\s+)', line))
    
    @staticmethod
    def _parse_section_header(line: str) -> Tuple[str, str]:
        """Extract section number and title from header"""
        import re
        match = re.match(r'^([\d\.]+)\s+(.+)', line)
        if match:
            return match.group(2), match.group(1)
        return line, ""
    
    @staticmethod
    def _fallback_chunking(text: str, chunk_size: int = 1000) -> List[dict]:
        """Fallback to fixed-size chunking if section detection fails"""
        chunks = []
        words = text.split()
        
        current_chunk = []
        for word in words:
            current_chunk.append(word)
            if len(' '.join(current_chunk)) >= chunk_size:
                chunks.append({
                    "section": f"{len(chunks) + 1}",
                    "title": "Untitled Section",
                    "text": ' '.join(current_chunk),
                    "start_page": 1,
                })
                current_chunk = []
        
        if current_chunk:
            chunks.append({
                "section": f"{len(chunks) + 1}",
                "title": "Untitled Section",
                "text": ' '.join(current_chunk),
                "start_page": 1,
            })
        
        return chunks
