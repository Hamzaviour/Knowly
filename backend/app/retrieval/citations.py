from typing import List, Dict, Any

class CitationEngine:
    """
    Builds verified citations linking claims in AI responses directly to
    source document ID, document title, page number, section, and char offsets.
    """
    
    @staticmethod
    def format_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        for c in chunks:
            citations.append({
                "citation_id": c.get("chunk_id") or c.get("id"),
                "document_id": c.get("document_id"),
                "document_title": c.get("document_title", "Document"),
                "source_title": c.get("document_title", "Document"),
                "page_number": c.get("page_number", 1),
                "section": c.get("section", "General"),
                "char_start": c.get("char_start", 0),
                "char_end": c.get("char_end", 0),
                "bbox": c.get("bbox", [0, 0, 0, 0]),
                "quote_snippet": c.get("content", "")[:250].strip() + ("..." if len(c.get("content", "")) > 250 else ""),
                "content": c.get("content", ""),
                "badge": f"[Source: {c.get('document_title', 'Doc')}, Page {c.get('page_number', 1)}]"
            })
        return citations
