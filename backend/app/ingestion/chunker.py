from typing import List, Dict, Any
import re

class LayoutAwareChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, parsed_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunks document text per page and section while preserving:
        - page_number
        - section header
        - character offsets (char_start, char_end)
        - chunk index
        """
        all_chunks = []
        global_chunk_idx = 0

        for page in parsed_pages:
            page_num = page.get("page_number", 1)
            text = page.get("text", "")
            sections = page.get("sections", [])
            
            if not text.strip():
                continue

            # Split text by paragraphs or double newlines
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
            
            current_chunk_text = ""
            current_section = sections[0]["title"] if sections else "Main Content"
            char_offset = 0

            for para in paragraphs:
                if len(current_chunk_text) + len(para) + 2 > self.chunk_size and current_chunk_text:
                    start_char = char_offset
                    end_char = start_char + len(current_chunk_text)
                    all_chunks.append({
                        "chunk_index": global_chunk_idx,
                        "content": current_chunk_text.strip(),
                        "page_number": page_num,
                        "section": current_section,
                        "char_start": start_char,
                        "char_end": end_char,
                        "bbox": page.get("bbox", [0, 0, 100, 100])
                    })
                    global_chunk_idx += 1
                    # Keep overlap
                    overlap_len = min(len(current_chunk_text), self.chunk_overlap)
                    current_chunk_text = current_chunk_text[-overlap_len:] + "\n\n" + para
                    char_offset += len(para)
                else:
                    if current_chunk_text:
                        current_chunk_text += "\n\n" + para
                    else:
                        current_chunk_text = para
                    char_offset += len(para)

            if current_chunk_text:
                all_chunks.append({
                    "chunk_index": global_chunk_idx,
                    "content": current_chunk_text.strip(),
                    "page_number": page_num,
                    "section": current_section,
                    "char_start": char_offset,
                    "char_end": char_offset + len(current_chunk_text),
                    "bbox": page.get("bbox", [0, 0, 100, 100])
                })
                global_chunk_idx += 1

        return all_chunks
