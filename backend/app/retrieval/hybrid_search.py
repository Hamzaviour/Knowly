from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import math

class HybridSearchEngine:
    """
    Executes parallel search across:
    1. Vector Similarity Search (Dense)
    2. BM25 Keyword Search (Sparse)
    3. Metadata & Knowledge Base Filtering
    Combines results via Reciprocal Rank Fusion (RRF).
    """
    
    def __init__(self, k_constant: int = 60):
        self.k_constant = k_constant

    def reciprocal_rank_fusion(self, vector_results: List[Dict[str, Any]], bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        scores = {}
        items_map = {}

        # Score vector results
        for rank, item in enumerate(vector_results):
            chunk_id = item["chunk_id"]
            items_map[chunk_id] = item
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (self.k_constant + rank + 1)

        # Score BM25 results
        for rank, item in enumerate(bm25_results):
            chunk_id = item["chunk_id"]
            if chunk_id not in items_map:
                items_map[chunk_id] = item
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (self.k_constant + rank + 1)

        # Sort by fused score
        fused = []
        for chunk_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            entry = dict(items_map[chunk_id])
            entry["rrf_score"] = score
            fused.append(entry)

        return fused

    def bm25_search(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 20) -> List[Dict[str, Any]]:
        if not chunks:
            return []
        
        corpus = [c["content"].lower().split() for c in chunks]
        bm25 = BM25Okapi(corpus)
        tokenized_query = query.lower().split()
        doc_scores = bm25.get_scores(tokenized_query)
        
        scored_chunks = []
        for idx, score in enumerate(doc_scores):
            if score > 0:
                item = dict(chunks[idx])
                item["bm25_score"] = float(score)
                scored_chunks.append(item)
                
        scored_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_chunks[:top_k]
