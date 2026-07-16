"""
retriever.py
------------
Recuperador de contexto basado en TF-IDF + similitud coseno.

Se eligió TF-IDF (scikit-learn) en lugar de embeddings neuronales para
mantener el despliegue en Render liviano y rápido de construir (sin
descargar modelos de embeddings ni depender de una base de datos vectorial
externa). Para un dataset de 5 documentos internos, TF-IDF ofrece muy
buena precisión sobre términos técnicos exactos (nombres de servicios,
siglas como SLA/SLO, patrones de diseño, etc.).
"""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.loaders import Chunk, load_knowledge_base

SPANISH_STOPWORDS = [
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
    "más", "o", "pero", "sus", "le", "ya", "o", "este", "sí", "porque",
    "esta", "entre", "cuando", "muy", "sin", "sobre", "también", "me",
    "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante",
    "ellos", "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo",
]


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class KnowledgeBaseRetriever:
    def __init__(self, knowledge_dir: str = "knowledge_base"):
        self.chunks: list[Chunk] = load_knowledge_base(knowledge_dir)
        if not self.chunks:
            raise RuntimeError(
                f"No se encontraron documentos en '{knowledge_dir}'. "
                "Verifica que existan archivos .txt o .csv en esa carpeta."
            )

        self.vectorizer = TfidfVectorizer(stop_words=SPANISH_STOPWORDS)
        self.matrix = self.vectorizer.fit_transform([c.text for c in self.chunks])

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.matrix).flatten()

        top_indices = similarities.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            results.append(RetrievedChunk(text=chunk.text, source=chunk.source, score=score))

        return results

    @property
    def document_count(self) -> int:
        return len({c.source for c in self.chunks})

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)
