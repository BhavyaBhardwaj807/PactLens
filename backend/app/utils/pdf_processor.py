"""
PactLens Backend - Utilities for PDF Processing
Extract text and metadata from PDF documents
"""

import PyPDF2
import os
from typing import Tuple, List
from pathlib import Path
import re


class PDFProcessor:
    """Process and extract text from PDF files"""

    @staticmethod
    def extract_text_and_metadata(file_path: str) -> Tuple[str, dict]:

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                full_text = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    full_text += f"\n--- Page {page_num + 1} ---\n"
                    page_text = page.extract_text() or ""
                    full_text += page_text

                metadata = {
                    "pages": num_pages,
                    "size": os.path.getsize(file_path),
                    "filename": Path(file_path).name,
                }

                return full_text, metadata

        except Exception as e:
            raise Exception(f"Error extracting PDF: {str(e)}")

    @staticmethod
    def chunk_by_sections(text: str, min_section_length: int = 30) -> List[dict]:

        chunks = []
        current_chunk = ""
        current_section = ""
        current_number = ""
        start_page = 1

        lines = text.split('\n')

        for line in lines:

            if '--- Page' in line:
                try:
                    page_num = int(line.split('Page ')[1].split(' ---')[0])
                    start_page = page_num
                except:
                    pass
                continue

            stripped = line.strip()

            # ✅ FIXED HERE
            if PDFProcessor._is_section_header(stripped):

                if current_chunk.strip() and len(current_chunk.strip()) > min_section_length:
                    chunks.append({
                        "section": current_number,
                        "title": current_section,
                        "text": current_chunk.strip(),
                        "start_page": start_page,
                    })

                # ✅ FIXED HERE
                current_section, current_number = PDFProcessor._parse_section_header(stripped)
                current_chunk = ""

            else:
                current_chunk += line + "\n"

        if current_chunk.strip() and len(current_chunk.strip()) > min_section_length:
            chunks.append({
                "section": current_number,
                "title": current_section,
                "text": current_chunk.strip(),
                "start_page": start_page,
            })

        # ✅ FIXED HERE
        return chunks if chunks else PDFProcessor._fallback_chunking(text)

    @staticmethod
    def _is_section_header(line: str) -> bool:
        if len(line) < 3 or len(line) > 200:
            return False

        return bool(re.match(r'^(\d+(\.\d+)*[\.\)]?\s+)', line))

    @staticmethod
    def _parse_section_header(line: str) -> Tuple[str, str]:
        match = re.match(r'^([\d\.]+)\s+(.+)', line)
        if match:
            return match.group(2), match.group(1)
        return line, ""

    @staticmethod
    def _fallback_chunking(text: str, chunk_size: int = 1000) -> List[dict]:

        chunks = []
        words = text.split()

        current_chunk = []

        for word in words:
            current_chunk.append(word)

            if len(' '.join(current_chunk)) >= chunk_size:
                chunks.append({
                    "section": str(len(chunks) + 1),
                    "title": "Untitled Section",
                    "text": ' '.join(current_chunk),
                    "start_page": 1,
                })
                current_chunk = []

        if current_chunk:
            chunks.append({
                "section": str(len(chunks) + 1),
                "title": "Untitled Section",
                "text": ' '.join(current_chunk),
                "start_page": 1,
            })

        return chunks
