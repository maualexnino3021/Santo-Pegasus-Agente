"""
Pruebas del retriever TF-IDF. No requieren ANTHROPIC_API_KEY porque no
llaman al modelo de lenguaje, solo verifican la recuperación de contexto.

Ejecutar con:
    pytest tests/
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.retriever import KnowledgeBaseRetriever  # noqa: E402


def test_loads_all_documents():
    retriever = KnowledgeBaseRetriever("knowledge_base")
    assert retriever.document_count == 5
    assert retriever.chunk_count > 0


def test_retrieves_relevant_chunk_for_incident_question():
    retriever = KnowledgeBaseRetriever("knowledge_base")
    results = retriever.retrieve("severidad SEV-1 incidente SLA", top_k=3)
    assert len(results) > 0
    sources = [r.source for r in results]
    assert "04_protocolo_incidentes_postmortems.txt" in sources


def test_retrieves_relevant_chunk_for_onboarding_question():
    retriever = KnowledgeBaseRetriever("knowledge_base")
    results = retriever.retrieve("primer día onboarding accesos cuentas", top_k=3)
    assert len(results) > 0
    sources = [r.source for r in results]
    assert "03_manual_onboarding_desarrolladores.txt" in sources


def test_empty_query_still_returns_list():
    retriever = KnowledgeBaseRetriever("knowledge_base")
    results = retriever.retrieve("xyz123 palabra inexistente inventada", top_k=3)
    assert isinstance(results, list)
