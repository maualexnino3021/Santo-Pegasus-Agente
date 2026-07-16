const KB_DOCS = [
  { key: "01_guia_ingenieria_backend.txt", label: "Guía Back-end" },
  { key: "02_guia_ingenieria_frontend.txt", label: "Guía Front-end" },
  { key: "03_manual_onboarding_desarrolladores.txt", label: "Onboarding" },
  { key: "04_protocolo_incidentes_postmortems.txt", label: "Incidentes / SRE" },
  { key: "05_arquitectura_microservicios.txt", label: "Microservicios" },
];

const messagesEl = document.getElementById("messages");
const composerEl = document.getElementById("composer");
const inputEl = document.getElementById("question-input");
const sendBtn = document.getElementById("send-btn");
const globalStatusDot = document.querySelector("#global-status .dot");
const globalStatusText = document.getElementById("global-status-text");
const kbStripEl = document.getElementById("kb-strip");

function renderKbStrip(activeSources = []) {
  kbStripEl.innerHTML = "";
  KB_DOCS.forEach((doc) => {
    const pill = document.createElement("span");
    pill.className = "kb-pill" + (activeSources.includes(doc.key) ? " active" : "");
    pill.innerHTML = `<span class="dot ${activeSources.includes(doc.key) ? "dot-ok" : "dot-pending"}"></span>${doc.label}`;
    kbStripEl.appendChild(pill);
  });
}

function appendMessage({ role, html, sources = [], isError = false }) {
  const wrapper = document.createElement("div");
  wrapper.className = `msg msg-${role}${isError ? " msg-error" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? "Tú" : "SP";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = html;

  if (sources.length) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "msg-sources";
    sources.forEach((src) => {
      const tag = document.createElement("span");
      tag.className = "source-tag";
      const doc = KB_DOCS.find((d) => d.key === src);
      tag.textContent = doc ? doc.label : src;
      sourcesEl.appendChild(tag);
    });
    bubble.appendChild(sourcesEl);
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  messagesEl.parentElement.scrollTop = messagesEl.parentElement.scrollHeight;
  return wrapper;
}

function appendTypingIndicator() {
  return appendMessage({
    role: "agent",
    html: '<span class="typing-dots"><span></span><span></span><span></span></span>',
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (res.ok && data.status === "ok") {
      globalStatusDot.className = "dot dot-ok";
      globalStatusText.textContent = `${data.documents} documentos · ${data.chunks} fragmentos`;
    } else {
      globalStatusDot.className = "dot dot-error";
      globalStatusText.textContent = "Agente no disponible";
    }
  } catch (err) {
    globalStatusDot.className = "dot dot-error";
    globalStatusText.textContent = "Sin conexión";
  }
}

composerEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = inputEl.value.trim();
  if (!question) return;

  appendMessage({ role: "user", html: `<p>${escapeHtml(question)}</p>` });
  inputEl.value = "";
  inputEl.disabled = true;
  sendBtn.disabled = true;

  const typingEl = appendTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    typingEl.remove();

    if (!res.ok) {
      appendMessage({
        role: "agent",
        html: `<p>${escapeHtml(data.error || "Ocurrió un error inesperado.")}</p>`,
        isError: true,
      });
      return;
    }

    appendMessage({
      role: "agent",
      html: `<p>${escapeHtml(data.answer).replace(/\n/g, "<br>")}</p>`,
      sources: data.sources || [],
    });
    renderKbStrip(data.sources || []);
  } catch (err) {
    typingEl.remove();
    appendMessage({
      role: "agent",
      html: "<p>No se pudo contactar al agente. Revisa tu conexión e inténtalo de nuevo.</p>",
      isError: true,
    });
  } finally {
    inputEl.disabled = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }
});

renderKbStrip();
checkHealth();
