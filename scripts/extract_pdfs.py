"""
extract_pdfs.py
----------------
Script OFFLINE para leer y procesar los documentos fuente (PDF) del agente.

No se ejecuta en producción (Render): se corre localmente una sola vez
(o cada vez que cambien los documentos fuente) para generar los archivos
de texto plano que sí se despliegan en `knowledge_base/`. Esto evita que
el servicio en Render dependa de binarios pesados como poppler/tesseract.

Uso:
    python scripts/extract_pdfs.py --input pdfs/ --output knowledge_base/

Estrategia de extracción:
    1. Intenta extraer el texto nativo del PDF con pypdf.
    2. Si una página no devuelve texto (PDF escaneado / imagen), la
       rasteriza con pdf2image y aplica OCR con pytesseract (idioma
       español, con fallback a inglés).
"""
import argparse
import os
import re
import sys

from pypdf import PdfReader


def clean_text(text: str) -> str:
    """Normaliza saltos de línea y colapsa espacios/afirmaciones repetidas del OCR."""
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_native_text(pdf_path: str) -> list[str]:
    """Devuelve una lista de strings, una por página, usando la capa de texto nativa."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return pages_text


def ocr_page(pdf_path: str, page_number: int, dpi: int = 200) -> str:
    """Rasteriza una página específica (1-indexed) y le aplica OCR."""
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(
        pdf_path, dpi=dpi, first_page=page_number, last_page=page_number
    )
    if not images:
        return ""
    try:
        return pytesseract.image_to_string(images[0], lang="spa")
    except Exception:
        # Si el paquete de idioma 'spa' no está instalado, usa inglés como fallback.
        return pytesseract.image_to_string(images[0], lang="eng")


def extract_document(pdf_path: str) -> str:
    """Extrae el texto completo de un PDF, usando OCR página por página cuando haga falta."""
    native_pages = extract_native_text(pdf_path)
    final_pages = []

    for i, page_text in enumerate(native_pages, start=1):
        if page_text and len(page_text.strip()) > 20:
            final_pages.append(page_text)
        else:
            print(f"  Página {i}: sin texto nativo, aplicando OCR...")
            final_pages.append(ocr_page(pdf_path, i))

    return clean_text("\n\n".join(final_pages))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="pdfs", help="Carpeta con los PDF de origen")
    parser.add_argument(
        "--output", default="knowledge_base", help="Carpeta destino para los .txt"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print(f"No se encontró la carpeta de entrada: {args.input}")
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)

    pdf_files = sorted(f for f in os.listdir(args.input) if f.lower().endswith(".pdf"))
    if not pdf_files:
        print(f"No se encontraron archivos PDF en {args.input}")
        sys.exit(1)

    for filename in pdf_files:
        pdf_path = os.path.join(args.input, filename)
        print(f"Procesando: {filename}")
        text = extract_document(pdf_path)

        out_name = os.path.splitext(filename)[0] + ".txt"
        out_path = os.path.join(args.output, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  -> Guardado en {out_path} ({len(text)} caracteres)")

    print("\nExtracción completa.")


if __name__ == "__main__":
    main()
