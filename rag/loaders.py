"""
loaders.py
----------
Lee los documentos de `knowledge_base/` (texto plano ya extraído de los PDF
originales, o archivos .csv) y los divide en fragmentos ("chunks") listos
para indexar con el retriever.
"""
import csv
import os
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str      # nombre del archivo de origen (se muestra como cita)
    chunk_id: int


def _split_into_chunks(text: str, max_chars: int = 900, overlap: int = 150) -> list[str]:
    """
    Divide un texto largo en fragmentos de tamaño acotado, respetando
    saltos de párrafo cuando es posible y añadiendo solapamiento entre
    fragmentos consecutivos para no perder contexto en los bordes.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 <= max_chars:
            current = f"{current}\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            # Si el propio párrafo es más largo que max_chars, lo partimos también
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars - overlap):
                    chunks.append(para[i : i + max_chars])
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    # Aplica solapamiento simple entre fragmentos consecutivos
    overlapped = []
    for i, c in enumerate(chunks):
        if i > 0 and overlap > 0:
            tail = chunks[i - 1][-overlap:]
            c = f"{tail}\n{c}"
        overlapped.append(c)

    return overlapped


def _load_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _load_csv(path: str) -> str:
    """Convierte cada fila de un CSV en una línea de texto 'columna: valor'."""
    rows_text = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line = "; ".join(f"{k}: {v}" for k, v in row.items() if v)
            rows_text.append(line)
    return "\n".join(rows_text)


def load_knowledge_base(directory: str) -> list[Chunk]:
    """Carga todos los .txt y .csv de `directory` y los devuelve como chunks indexables."""
    chunks: list[Chunk] = []
    chunk_id = 0

    if not os.path.isdir(directory):
        return chunks

    for filename in sorted(os.listdir(directory)):
        path = os.path.join(directory, filename)
        if filename.lower().endswith(".txt"):
            text = _load_txt(path)
        elif filename.lower().endswith(".csv"):
            text = _load_csv(path)
        else:
            continue

        for piece in _split_into_chunks(text):
            chunks.append(Chunk(text=piece, source=filename, chunk_id=chunk_id))
            chunk_id += 1

    return chunks
