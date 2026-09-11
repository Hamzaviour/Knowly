from typing import Dict, Any, List, Optional
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
        comparison_docs: Dict[str, Any] = None,
        api_keys: Dict[str, str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        document_chunks = document_chunks or []
        conversation_history = conversation_history or []
        
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

        # If keyword search returned 0 matches but documents exist in workspace,
        # fallback to top workspace document chunks (critical for "explain", "tell me what is in it", "summarize", etc.)
        if not bm25_res and document_chunks:
            bm25_res = document_chunks[:15]

        reranked = ContextualReranker.rerank(query, bm25_res, top_n=8)
        if not reranked and bm25_res:
            reranked = bm25_res[:5]

        citations = CitationEngine.format_citations(reranked)
        
        # Build context from full retrieved chunks
        context_str = "\n\n".join([f"{c['badge']}:\n{c.get('content') or c.get('quote_snippet', '')}" for c in citations])

        # Include list of distinct documents available in workspace
        doc_titles = list(dict.fromkeys([c.get("document_title", "Document") for c in document_chunks if c.get("document_title")]))
        doc_catalog_str = f"Indexed Workspace Documents: {', '.join(doc_titles)}" if doc_titles else "No documents indexed"
        
        # Build messages: system + conversation history + current user message with context
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are Knowly AI, an advanced document intelligence assistant. "
                    f"{doc_catalog_str}. "
                    "Answer accurately and naturally based on the provided context. "
                    "When the user asks a follow-up question (e.g. 'only show grade B', 'filter by X', 'now list only...'), "
                    "you MUST honour that instruction and work from the previous answer and context. "
                    "Cite sources as [Source: Document, Page X]. "
                    "Never ignore follow-up filter or refinement instructions."
                )
            }
        ]

        # Inject prior conversation turns so the model understands follow-up intent
        # Limit history to avoid token overflow — keep last 6 exchanges (12 messages)
        for hist_msg in conversation_history[-12:]:
            messages.append({"role": hist_msg["role"], "content": hist_msg["content"]})

        # Add current user turn with retrieved document context
        messages.append({
            "role": "user",
            "content": f"Context:\n{context_str}\n\nQuestion: {query}"
        })
        
        llm_res = await LLMRouter.generate_response(messages, task_type="standard", api_keys=api_keys)
        
        return {
            "answer": llm_res["content"],
            "citations": citations,
            "model_used": llm_res["model"],
            "tokens": llm_res["tokens"],
            "cost_usd": llm_res["cost_usd"],
            "retrieved_chunks_count": len(reranked)
        }
