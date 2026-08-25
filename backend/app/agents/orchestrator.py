from typing import Dict, Any, List
from app.agents.analyst_agent import AnalystAgent
from app.agents.comparison_agent import DocumentComparisonAgent
from app.agents.deep_research import DeepResearchEngine
from app.retrieval.query_analyzer import QueryAnalyzer
from app.retrieval.hybrid_search import HybridSearchEngine
from app.retrieval.reranker import ContextualReranker
from app.retrieval.citations import CitationEngine
from app.llm.router import LLMRouter

class AgentOrchestrator:
    """
    Autonomous AI Planner that decomposes user intent and routes to specialized agents:
    - Deep Research Mode
    - Document Comparison Agent
    - Tabular Analyst Agent
    - Hybrid RAG Retrieval Engine
    """
    
    @classmethod
    async def process_request(
        cls,
        query: str,
        mode: str = "standard",
        document_chunks: List[Dict[str, Any]] = None,
        comparison_docs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        document_chunks = document_chunks or []
        
        # 1. Mode: Document Comparison
        if mode == "compare" and comparison_docs:
            return DocumentComparisonAgent.compare_documents(
                comparison_docs.get("doc1_title", "Document 1"),
                comparison_docs.get("doc1_text", ""),
                comparison_docs.get("doc2_title", "Document 2"),
                comparison_docs.get("doc2_text", "")
            )
            
        # 2. Mode: Deep Research
        if mode == "deep_research":
            return DeepResearchEngine.conduct_research(query, document_chunks)
            
        # 3. Standard / Analyst Agentic RAG
        query_info = QueryAnalyzer.decompose_and_expand(query)
        hybrid = HybridSearchEngine()
        bm25_res = hybrid.bm25_search(query, document_chunks, top_k=20)
        reranked = ContextualReranker.rerank(query, bm25_res, top_n=5)
        citations = CitationEngine.format_citations(reranked)
        
        # Build context
        context_str = "\n\n".join([f"{c['badge']}:\n{c['quote_snippet']}" for c in citations])
        
        messages = [
            {"role": "system", "content": "You are Knowly AI, an advanced document intelligence assistant. Answer accurately based on context, and cite sources as [Source: Document, Page X]."},
            {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
        ]
        
        llm_res = await LLMRouter.generate_response(messages, task_type="standard")
        
        return {
            "answer": llm_res["content"],
            "citations": citations,
            "model_used": llm_res["model"],
            "tokens": llm_res["tokens"],
            "cost_usd": llm_res["cost_usd"],
            "retrieved_chunks_count": len(reranked)
        }
