from docx import Document as DocxDoc
from typing import List, Dict, Any

class DOCXParser:
    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        doc = DocxDoc(file_path)
        full_text = []
        sections = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style.name.startswith("Heading"):
                sections.append({"title": text, "offset": len("\n".join(full_text))})
            full_text.append(text)
            
        # Parse docx tables
        table_texts = []
        for table in doc.tables:
            table_data = []
            for row in table.rows:
                table_data.append([cell.text.strip() for cell in row.cells])
            if table_data:
                table_texts.append("\n".join([" | ".join(r) for r in table_data]))

        combined_text = "\n\n".join(full_text)
        if table_texts:
            combined_text += "\n\n--- Extracted Tables ---\n" + "\n\n".join(table_texts)

        return [{
            "page_number": 1,
            "text": combined_text,
            "sections": sections or [{"title": "Document Content", "offset": 0}],
            "bbox": [0, 0, 0, 0]
        }]
