import pypdf
from typing import List, Dict, Any
import os

class PDFParser:
    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        pages = []
        try:
            reader = pypdf.PdfReader(file_path)
            total_pages = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append({
                    "page_number": idx + 1,
                    "text": text,
                    "sections": [{"title": f"Page {idx+1}", "offset": 0}],
                    "bbox": [0, 0, 612, 792] # Standard letter dimensions
                })
        except Exception as e:
            pages.append({
                "page_number": 1,
                "text": f"Error parsing PDF: {str(e)}",
                "sections": [],
                "bbox": [0, 0, 0, 0]
            })
        return pages
