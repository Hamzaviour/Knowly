from typing import List, Dict, Any

class ContextualReranker:
    """
    Evaluates: 'How relevant is this chunk specifically to this question?'
    Filters and reranks top-50 candidate chunks down to top 5-10 high-precision chunks.
    """
    
    @staticmethod
    def rerank(query: str, candidates: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        if not candidates:
            return []
            
        query_words = set(query.lower().split())
        scored = []
        
        for cand in candidates:
            content = cand.get("content", "").lower()
            # Exact phrase matching bonus
            phrase_bonus = 2.0 if query.lower() in content else 0.0
            # Term density score
            matched_terms = sum(1 for w in query_words if w in content)
            term_ratio = matched_terms / max(1, len(query_words))
            
            # Base score from hybrid retrieval (rrf_score or bm25_score)
            base_score = cand.get("rrf_score", 0.1) * 10
            final_score = base_score + (term_ratio * 3.0) + phrase_bonus
            
            scored.append({
                **cand,
                "rerank_score": round(final_score, 4)
            })
            
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_n]
