"""
app.py
------
Aplicación Flask que expone:
  - GET  /            -> interfaz de chat (HTML)
  - POST /api/chat     -> {"question": "..."} -> {"answer": "...", "sources": [...]}
  - GET  /api/health    -> healthcheck para Render

El agente (rag/agent.py) se inicializa una sola vez al arrancar el proceso,
para no reconstruir el índice TF-IDF en cada request.
"""
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("santo-pegasus-agente")

app = Flask(__name__)

_agent = None
_agent_error = None


def get_agent():
    """Inicializa el agente de forma perezosa (lazy) y lo cachea en memoria."""
    global _agent, _agent_error
    if _agent is None and _agent_error is None:
        try:
            from rag.agent import SantoPegasusAgent

            _agent = SantoPegasusAgent()
            logger.info(
                "Agente inicializado: %s documentos, %s fragmentos indexados",
                _agent.retriever.document_count,
                _agent.retriever.chunk_count,
            )
        except Exception as exc:  # noqa: BLE001
            _agent_error = str(exc)
            logger.error("Error al inicializar el agente: %s", exc)
    return _agent, _agent_error


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    agent, error = get_agent()
    if error:
        return jsonify({"status": "error", "detail": error}), 500
    return jsonify(
        {
            "status": "ok",
            "documents": agent.retriever.document_count,
            "chunks": agent.retriever.chunk_count,
            "model": agent.model,
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()

    if not question:
        return jsonify({"error": "El campo 'question' es obligatorio."}), 400

    agent, error = get_agent()
    if error:
        return (
            jsonify(
                {
                    "error": (
                        "El agente no está disponible. Verifica la variable "
                        "de entorno ANTHROPIC_API_KEY."
                    ),
                    "detail": error,
                }
            ),
            500,
        )

    try:
        result = agent.ask(question)
        return jsonify(result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error procesando la pregunta")
        return jsonify({"error": "Ocurrió un error procesando la pregunta.", "detail": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
