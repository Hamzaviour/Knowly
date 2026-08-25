from typing import List, Dict, Any
import re

class QueryAnalyzer:
    """
    Analyzes user queries for:
    1. Query Rewriting (making implicit references explicit)
    2. Query Expansion (synonyms, technical terms)
    3. Query Decomposition (breaking complex multi-part queries into sub-questions)
    """
    
    @staticmethod
    def decompose_and_expand(query: str) -> Dict[str, Any]:
        cleaned_query = query.strip()
        
        # Detect multi-part questions (e.g. "Compare X and Y, and tell me Z")
        sub_queries = []
        if " and " in cleaned_query.lower() or " vs " in cleaned_query.lower() or " compared to " in cleaned_query.lower():
            parts = re.split(r'\b(?:and|vs|compared to|additionally|also)\b', cleaned_query, flags=re.IGNORECASE)
            sub_queries = [p.strip() for p in parts if len(p.strip()) > 3]
        
        if not sub_queries:
            sub_queries = [cleaned_query]

        # Query Expansion Keywords
        keywords = re.findall(r'\b[A-Za-z0-9_-]{3,}\b', cleaned_query.lower())
        
        return {
            "original_query": cleaned_query,
            "rewritten_query": cleaned_query,
            "sub_queries": sub_queries,
            "keywords": list(set(keywords)),
            "is_comparison": any(k in cleaned_query.lower() for k in ["compare", "difference", "versus", "vs", "changes", "between"]),
            "is_tabular_calc": any(k in cleaned_query.lower() for k in ["highest", "lowest", "sum", "average", "total", "revenue", "quarter", "max", "min"])
        }
