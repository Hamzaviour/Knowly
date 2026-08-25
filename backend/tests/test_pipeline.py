import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.table_parser import TableIntelligenceEngine
from app.ingestion.chunker import LayoutAwareChunker
from app.retrieval.query_analyzer import QueryAnalyzer
from app.retrieval.hybrid_search import HybridSearchEngine
from app.retrieval.reranker import ContextualReranker
from app.retrieval.citations import CitationEngine
from app.agents.comparison_agent import DocumentComparisonAgent

def test_query_analyzer():
    res = QueryAnalyzer.decompose_and_expand("Compare Q3 and Q4 revenue and find differences")
    assert res["is_comparison"] is True
    assert len(res["sub_queries"]) >= 1
    print("Query Analyzer Test Passed")

def test_chunker_and_citations():
    pages = [{"page_number": 1, "text": "This is paragraph 1.\n\nThis is paragraph 2.", "sections": [{"title": "Intro"}]}]
    chunker = LayoutAwareChunker()
    chunks = chunker.chunk_document(pages)
    assert len(chunks) >= 1
    
    citations = CitationEngine.format_citations(chunks)
    assert len(citations) == len(chunks)
    print("Chunker & Citations Test Passed")

def test_document_comparison():
    doc1 = "The payment term is 30 days. Termination requires 30 days notice."
    doc2 = "The payment term is 45 days. Termination requires 60 days notice."
    res = DocumentComparisonAgent.compare_documents("Contract V1", doc1, "Contract V2", doc2)
    assert res["changes_summary"]["similarity_ratio"] < 1.0
    print("Document Comparison Test Passed")

if __name__ == "__main__":
    test_query_analyzer()
    test_chunker_and_citations()
    test_document_comparison()
    print("All core engine tests passed successfully!")
