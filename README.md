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