from typing import List, Dict, Any

class OCRParser:
    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        # Lightweight fallback/pluggable OCR parser
        return [{
            "page_number": 1,
            "text": f"[Scanned/Image Document Processed: {file_path}]",
            "sections": [{"title": "OCR Extracted Text", "offset": 0}],
            "bbox": [0, 0, 800, 600]
        }]
