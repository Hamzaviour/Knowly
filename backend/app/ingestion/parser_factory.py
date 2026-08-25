from typing import List, Dict, Any
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.docx_parser import DOCXParser
from app.ingestion.pptx_parser import PPTXParser
from app.ingestion.table_parser import TableIntelligenceEngine
from app.ingestion.ocr_parser import OCRParser
import os

class DocumentParserFactory:
    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            pages = PDFParser.parse(file_path)
            return {"file_type": "pdf", "pages": pages, "is_tabular": False}
        elif ext in [".docx", ".doc"]:
            pages = DOCXParser.parse(file_path)
            return {"file_type": "docx", "pages": pages, "is_tabular": False}
        elif ext in [".pptx", ".ppt"]:
            pages = PPTXParser.parse(file_path)
            return {"file_type": "pptx", "pages": pages, "is_tabular": False}
        elif ext in [".xlsx", ".xls", ".csv"]:
            table_info = TableIntelligenceEngine.parse_spreadsheet(file_path)
            pages = [{
                "page_number": 1,
                "text": table_info["text_representation"],
                "sections": [{"title": "Spreadsheet Overview", "offset": 0}],
                "bbox": [0, 0, 0, 0]
            }]
            return {
                "file_type": "xlsx" if "xls" in ext else "csv",
                "pages": pages,
                "is_tabular": True,
                "table_metadata": table_info["sheets"]
            }
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            pages = OCRParser.parse(file_path)
            return {"file_type": "image", "pages": pages, "is_tabular": False}
        else:
            # Fallback plain text read
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            pages = [{
                "page_number": 1,
                "text": content,
                "sections": [{"title": "Text File", "offset": 0}],
                "bbox": [0, 0, 0, 0]
            }]
            return {"file_type": "text", "pages": pages, "is_tabular": False}
