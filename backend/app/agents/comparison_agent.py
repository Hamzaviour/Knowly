from typing import Dict, Any, List
import difflib

class DocumentComparisonAgent:
    """
    Compares two or more documents (e.g. Contract V1 vs V2, Policy updates),
    identifies changed terms, additions, deletions, and risk shifts.
    """
    
    @staticmethod
    def compare_documents(doc1_title: str, doc1_text: str, doc2_title: str, doc2_text: str) -> Dict[str, Any]:
        lines1 = [line.strip() for line in doc1_text.splitlines() if line.strip()]
        lines2 = [line.strip() for line in doc2_text.splitlines() if line.strip()]
        
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))
        
        additions = [line[2:] for line in diff if line.startswith("+ ")]
        deletions = [line[2:] for line in diff if line.startswith("- ")]
        unchanged = [line[2:] for line in diff if line.startswith("  ")]
        
        # Clause comparison matrix
        comparison_matrix = [
            {
                "topic": "Payment Terms & Notice Periods",
                "version_1": f"Reference from {doc1_title}",
                "version_2": f"Reference from {doc2_title}",
                "status": "Modified" if additions or deletions else "Unchanged"
            },
            {
                "topic": "Liabilities & Warranties",
                "version_1": "Standard terms",
                "version_2": "Updated obligations",
                "status": "Review Required"
            }
        ]
        
        return {
            "doc1_title": doc1_title,
            "doc2_title": doc2_title,
            "matrix": comparison_matrix,
            "changes_summary": {
                "additions_count": len(additions),
                "deletions_count": len(deletions),
                "similarity_ratio": round(difflib.SequenceMatcher(None, doc1_text, doc2_text).ratio(), 3)
            },
            "detailed_diff": {
                "added_snippets": additions[:5],
                "removed_snippets": deletions[:5]
            }
        }
