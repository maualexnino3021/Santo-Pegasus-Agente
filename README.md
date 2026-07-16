# Agente Inteligente — Santo Pegasus Soluciones

Agente conversacional (RAG) que responde preguntas sobre la documentación interna de
**Santo Pegasus Soluciones**, la empresa detrás de *Agendio*, una plataforma SaaS de
agendamiento de consultas médicas. El agente responde exclusivamente en base al
contenido de 5 documentos internos de ingeniería: guías de Back-end y Front-end,
manual de onboarding, protocolo de incidentes/post-mortems (SRE) y arquitectura de
microservicios.

Proyecto desarrollado para el **Challenge Alura Agente**, con despliegue en **Render**.

🔗 **Demo desplegada:** `<https://santo-pegasus-agente.onrender.com/>`
📸 **Captura del despliegue:** ver docs/screenshot-deploy.png

---

## Índice

- [Agente Inteligente — Santo Pegasus Soluciones](#agente-inteligente--santo-pegasus-soluciones)
  - [Índice](#índice)
  - [Descripción general](#descripción-general)
    - [Documentos que componen la base de conocimiento](#documentos-que-componen-la-base-de-conocimiento)
  - [Arquitectura de la solución](#arquitectura-de-la-solución)
  - [Tecnologías y herramientas](#tecnologías-y-herramientas)
    - [Elegir proveedor de LLM: Anthropic (Claude) u OpenAI (GPT)](#elegir-proveedor-de-llm-anthropic-claude-u-openai-gpt)
  - [Estructura del repositorio](#estructura-del-repositorio)
  - [Cómo ejecutar el proyecto localmente](#cómo-ejecutar-el-proyecto-localmente)
    - [Requisitos previos](#requisitos-previos)
    - [Pasos](#pasos)
  - [Cómo desplegar en Render](#cómo-desplegar-en-render)
    - [Opción A — Usando el Blueprint (`render.yaml`), recomendada](#opción-a--usando-el-blueprint-renderyaml-recomendada)
    - [Opción B — Configuración manual desde el Dashboard](#opción-b--configuración-manual-desde-el-dashboard)
  - [Regenerar la base de conocimiento (OCR/PDF)](#regenerar-la-base-de-conocimiento-ocrpdf)
  - [Ejemplos de preguntas y respuestas](#ejemplos-de-preguntas-y-respuestas)
  - [Pruebas](#pruebas)
  - [Licencia y uso](#licencia-y-uso)

---

## Descripción general

El agente implementa el patrón **RAG (Retrieval-Augmented Generation)**:

1. El usuario hace una pregunta en la interfaz de chat.
2. El sistema busca, dentro de la base de conocimiento indexada, los fragmentos de
   texto más relevantes para esa pregunta.
3. Esos fragmentos se inyectan como contexto en el prompt enviado al modelo de
   lenguaje (Claude), junto con instrucciones estrictas de responder **solo** con
   información presente en el contexto.
4. El modelo genera una respuesta en español, citando el/los documento(s) de origen.

Esto evita alucinaciones: si la pregunta no puede responderse con los documentos
disponibles, el agente lo indica explícitamente en vez de inventar una respuesta.

### Documentos que componen la base de conocimiento

| Archivo | Contenido |
|---|---|
| `01_guia_ingenieria_backend.txt` | Principios SOLID/DRY/KISS/YAGNI, arquitectura en capas, patrones de diseño, Spring Boot |
| `02_guia_ingenieria_frontend.txt` | Stack de front-end, arquitectura de componentes, gestión de estado, estándares de código |
| `03_manual_onboarding_desarrolladores.txt` | Bienvenida institucional, accesos, configuración del entorno local |
| `04_protocolo_incidentes_postmortems.txt` | Severidades (SEV-1 a SEV-4), SLAs, rollback en Docker/AWS ECS, post-mortems, SLI/SLO/Error Budget |
| `05_arquitectura_microservicios.txt` | Catálogo de microservicios, mapa de dependencias, patrones de comunicación, seguridad entre servicios |

> Los `.txt` de `knowledge_base/` son el resultado de procesar los 5 PDF originales
> (varios de ellos documentos escaneados) con extracción de texto nativo + OCR. Ver
> [Regenerar la base de conocimiento](#regenerar-la-base-de-conocimiento-ocrpdf).

---

## Arquitectura de la solución

```
┌─────────────────────┐      1. Pregunta del usuario
│  Interfaz de Chat    │ ───────────────────────────────┐
│  (HTML/CSS/JS)       │                                 │
└─────────────────────┘                                 ▼
        ▲                                     ┌───────────────────┐
        │ 4. Respuesta + fuentes citadas       │   Flask (app.py)   │
        └───────────────────────────────────── │   POST /api/chat   │
                                                └─────────┬──────────┘
                                                          │
                                     2. Recupera contexto │
                                                          ▼
                                          ┌───────────────────────────┐
                                          │  Retriever TF-IDF          │
                                          │  (rag/retriever.py)        │
                                          │  scikit-learn + cosine sim │
                                          └─────────────┬──────────────┘
                                                         │ fragmentos relevantes
                                                         ▼
                                          ┌───────────────────────────┐
                                          │  knowledge_base/*.txt       │
                                          │  (5 documentos indexados)   │
                                          └───────────────────────────┘
                                                          │
                                     3. Prompt + contexto │
                                                          ▼
                                          ┌───────────────────────────┐
                                          │  Claude API (Anthropic)    │
                                          │  rag/agent.py               │
                                          └───────────────────────────┘
```

**Decisiones de diseño clave:**

- **Retrieval con TF-IDF en vez de embeddings neuronales**: con solo 5 documentos
  internos, TF-IDF (`scikit-learn`) da muy buena precisión sobre términos técnicos
  exactos (SEV-1, SLA, nombres de microservicios, siglas) y evita depender de una
  base de datos vectorial externa o de descargar modelos de embeddings pesados,
  lo que mantiene el despliegue en Render liviano y rápido.
- **Extracción de PDF desacoplada del runtime**: los PDF originales (algunos
  escaneados) se procesan **una sola vez, offline**, con `scripts/extract_pdfs.py`
  (texto nativo + OCR de respaldo). El resultado (`knowledge_base/*.txt`) es lo que
  se despliega; así Render no necesita instalar `poppler`/`tesseract`.
- **Sin base de datos**: el índice TF-IDF se construye en memoria al arrancar el
  proceso (segundos), suficiente para el volumen de documentos del challenge.
- **Proveedor de LLM intercambiable**: `rag/llm_providers.py` abstrae la llamada al
  modelo de lenguaje. Podés usar **Claude (Anthropic)** u **OpenAI** simplemente
  cambiando la variable de entorno `LLM_PROVIDER`, sin tocar el resto del código.

---

## Tecnologías y herramientas

- **Python 3.11**
- **Flask** — servidor web y API REST
- **Gunicorn** — servidor WSGI de producción
- **scikit-learn** — vectorización TF-IDF y similitud coseno para el retriever
- **Anthropic API (Claude) u OpenAI API (GPT)** — generación de las respuestas del
  agente, intercambiable vía `LLM_PROVIDER` (ver abajo)
- **pypdf / pdf2image / pytesseract** — extracción de texto y OCR (solo en el script offline de ingesta)
- **HTML/CSS/JavaScript vanilla** — interfaz de chat
- **Render** — plataforma de despliegue (Web Service)
- **pytest** — pruebas automatizadas del retriever

### Elegir proveedor de LLM: Anthropic (Claude) u OpenAI (GPT)

El proyecto soporta ambos proveedores sin cambiar código, solo variables de entorno:

| Variable | Para Anthropic | Para OpenAI |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` (por defecto) | `openai` |
| Clave de API | `ANTHROPIC_API_KEY` | `OPENAI_API_KEY` |
| Modelo | `CLAUDE_MODEL` (ej. `claude-sonnet-4-5`) | `OPENAI_MODEL` (ej. `gpt-4o-mini`, `gpt-4o`) |

Por ejemplo, para usar OpenAI en local, tu `.env` debe tener:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

Solo necesitas configurar las variables del proveedor que vayas a usar (no hace
falta tener ambas claves).

---

## Estructura del repositorio

```
santo-pegasus-agente/
├── app.py                          # App Flask: rutas /, /api/chat, /api/health
├── rag/
│   ├── agent.py                    # Orquestación RAG + llamada a Claude
│   ├── retriever.py                # Índice TF-IDF y recuperación de contexto
│   └── loaders.py                  # Carga y "chunking" de knowledge_base/*.txt y .csv
├── knowledge_base/                 # Documentos ya extraídos (texto plano), listos para indexar
│   ├── 01_guia_ingenieria_backend.txt
│   ├── 02_guia_ingenieria_frontend.txt
│   ├── 03_manual_onboarding_desarrolladores.txt
│   ├── 04_protocolo_incidentes_postmortems.txt
│   └── 05_arquitectura_microservicios.txt
├── scripts/
│   └── extract_pdfs.py             # Script offline: PDF -> texto (con OCR de respaldo)
├── templates/
│   └── index.html                  # Interfaz de chat
├── static/
│   ├── style.css
│   └── chat.js
├── tests/
│   └── test_retriever.py           # Pruebas automatizadas (no requieren API key)
├── requirements.txt                # Dependencias de runtime (Render)
├── requirements-ingest.txt         # Dependencias solo para el script de extracción/OCR
├── render.yaml                     # Blueprint de despliegue en Render
├── .env.example
└── .gitignore
```

---

## Cómo ejecutar el proyecto localmente

### Requisitos previos

- Python 3.11+
- Una API key de Anthropic ([console.anthropic.com](https://console.anthropic.com/settings/keys))

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/santo-pegasus-agente.git
cd santo-pegasus-agente

# 2. Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env y coloca tu ANTHROPIC_API_KEY

# 5. Ejecutar la aplicación
python app.py
```

La aplicación quedará disponible en `http://localhost:5000`.

---

## Cómo desplegar en Render

### Opción A — Usando el Blueprint (`render.yaml`), recomendada

1. Sube el repositorio a GitHub (público).
2. En el [Dashboard de Render](https://dashboard.render.com/), haz clic en
   **New +** → **Blueprint**.
3. Conecta tu repositorio de GitHub. Render detectará automáticamente `render.yaml`.
4. Cuando se te solicite, completa la variable de entorno `ANTHROPIC_API_KEY` con tu
   clave real (está marcada como `sync: false` en el blueprint, por lo que Render
   la pedirá de forma segura y no quedará en el repositorio).
5. Haz clic en **Apply**. Render instalará las dependencias y desplegará el servicio.
6. Una vez desplegado, visita la URL pública que Render asigna
   (`https://santo-pegasus-agente.onrender.com` o similar) y prueba el chat.

### Opción B — Configuración manual desde el Dashboard

1. **New +** → **Web Service** → conecta el repositorio.
2. Configura:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
3. En la sección **Environment**, agrega:
   - `ANTHROPIC_API_KEY` → tu clave de Anthropic
   - `CLAUDE_MODEL` → `claude-sonnet-4-5` (o el modelo vigente que prefieras)
4. Despliega y espera a que el estado sea **Live**.

> **Nota sobre el plan gratuito de Render:** los servicios free "duermen" tras un
> período de inactividad y tardan unos segundos en responder al primer request
> después de estar inactivos. Esto es normal y no indica un error.

---

## Regenerar la base de conocimiento (OCR/PDF)

Los archivos en `knowledge_base/*.txt` ya están listos para usarse: **no necesitas
volver a correr esto para desplegar el proyecto.** Este paso solo es necesario si
reemplazas los PDF originales por nuevas versiones.

```bash
# Instala las dependencias de ingesta (solo local, no en Render)
pip install -r requirements-ingest.txt

# Instala los binarios del sistema necesarios para OCR:
#   macOS:   brew install poppler tesseract tesseract-lang
#   Ubuntu:  sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-spa

# Coloca tus PDF en una carpeta "pdfs/" y ejecuta:
python scripts/extract_pdfs.py --input pdfs/ --output knowledge_base/
```

El script intenta primero extraer el texto nativo del PDF (`pypdf`); si una página
no tiene texto extraíble (documento escaneado), la rasteriza y le aplica OCR en
español con `pytesseract` como respaldo automático.

---

## Ejemplos de preguntas y respuestas

> Respuestas generadas por el agente contra la base de conocimiento real del
> proyecto. La redacción exacta puede variar levemente entre ejecuciones, pero el
> contenido y la fuente citada se mantienen consistentes.

**Pregunta:** *¿Cuál es el SLA de respuesta para un incidente clasificado como SEV-1?*

> **Respuesta del agente:** Según el Protocolo de Respuesta a Incidentes y
> Post-Mortems, un incidente SEV-1 (Crítico, que afecta al sistema Agendio en su
> totalidad) tiene un SLA de respuesta de 15 minutos, con actualizaciones de estado
> cada 30 minutos hasta su resolución.
> *Fuente: `04_protocolo_incidentes_postmortems.txt`*

**Pregunta:** *¿Qué debo hacer el primer día como nuevo desarrollador en Santo Pegasus?*

> **Respuesta del agente:** El Manual de Onboarding indica que el Día 1 está
> dedicado a Accesos y Cuentas: debes confirmar que recibiste tu correo corporativo
> (con al menos 48 horas de anticipación) y, si no lo tienes al llegar, contactar al
> equipo de People. El objetivo es que, al finalizar la primera semana, tengas tu
> entorno configurado y estés listo para contribuir.
> *Fuente: `03_manual_onboarding_desarrolladores.txt`*

**Pregunta:** *¿Qué principios de ingeniería son obligatorios en el desarrollo back-end?*

> **Respuesta del agente:** La Guía de Ingeniería Back-end establece como
> obligatorios los principios SOLID (con énfasis en Single Responsibility y
> Dependency Inversion mediante inyección de dependencias de Spring), además de DRY,
> KISS y YAGNI. También exige una arquitectura en capas (Controllers, Services,
> Repositories) y el uso de DTOs para nunca exponer entidades de base de datos
> directamente en la API.
> *Fuente: `01_guia_ingenieria_backend.txt`*

**Pregunta:** *¿Cuál es la capital de Francia?* (fuera del alcance del agente)

> **Respuesta del agente:** No encontré información relacionada con tu pregunta en
> la base de conocimiento de Santo Pegasus Soluciones. Intenta reformularla o
> consulta directamente con el equipo correspondiente.

---

## Pruebas

```bash
pip install pytest
pytest tests/ -v
```

Las pruebas verifican el retriever (carga de documentos y recuperación de contexto
relevante) y **no requieren `ANTHROPIC_API_KEY`**, ya que no invocan al modelo de
lenguaje.

---

## Licencia y uso

Proyecto desarrollado con fines educativos para el Challenge Alura Agente. Los
documentos de `knowledge_base/` son contenido ficticio creado para el ejercicio.

Este proyecto se distribuye bajo la licencia MIT (ver archivo `LICENSE`). Si
reutilizas o adaptas este código, se agradece mencionar al autor original.

**Autor:** Mauricio Niño Gamboa — [GitHub: maualexnino3021](https://github.com/maualexnino3021)