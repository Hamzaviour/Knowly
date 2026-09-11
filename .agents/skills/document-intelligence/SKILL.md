---
name: document-intelligence
description: Complete workflow guide and capabilities of the Knowly Document AI Workspace platform.
---

# Knowly Document AI Workspace Workflow Guide

Knowly is an enterprise document intelligence and AI workspace platform.

## Architecture
- **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS with Bright 3D Theme, Radix UI.
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy, SQLite / PostgreSQL, Qdrant vector retrieval, BM25 Hybrid Search, Contextual Reranker, Agent Orchestrator.

## Core Features
1. **Document Ingestion & Chunker**:
   - Layout-aware parser supporting PDF, DOCX, PPTX, XLSX, TXT, and images.
   - Table detection and extraction for structured analysis.
2. **Chat & Agent Orchestrator**:
   - Standard RAG with citations, page numbers, and bounding boxes.
   - Deep Research multi-step planning and cross-document synthesis.
   - Tabular Analyst with deterministic Pandas execution.
   - Document Comparison with diff highlighting and clause matrix.
3. **Report Generation**:
   - Live Markdown editor with split preview and instant export to Markdown, DOCX, PDF, HTML.
4. **Workflows & Automation**:
   - Event triggers (on upload, schedule, manual) running pipeline actions.
5. **Subscription & Billing**:
   - Free and Pro tiers, Stripe checkout, quota management.
