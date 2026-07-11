const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#message");
const sendButton = document.querySelector("#sendButton");
const quickPrompts = document.querySelector("#quickPrompts");
const apiStatus = document.querySelector("#apiStatus");
const resetButton = document.querySelector("#resetChat");

const MAX_HISTORY = 12;
const WELCOME =
  "Hola, soy AndesBot 👋 Puedo ayudarte con paquetes, precios, pagos, reservas, documentos y politicas de Viajes Andes. ¿Que quieres saber?";

let history = [];

const prompts = [
  "Puedo pagar con Nequi?",
  "Cuanto debo pagar para reservar?",
  "Me devuelven la plata si cancelo?",
  "Cuanto cuesta un viaje a Japon?",
  "Tienen cruceros?",
  "Hay descuentos para grupos?"
];

function addMessage(text, role, sources = []) {
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  if (role === "bot") {
    const avatar = document.createElement("span");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "⛰";
    wrapper.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const paragraph = document.createElement("p");

      if (/^#{1,4}\s/.test(line)) {
        paragraph.className = "para-title";
        line = line.replace(/^#{1,4}\s+/, "");
      } else if (line.startsWith("- ") || line.startsWith("* ")) {
        paragraph.className = "para-item";
        line = "• " + line.slice(2);
      }

      line.split("**").forEach((part, index) => {
        if (!part) return;
        if (index % 2 === 1) {
          const bold = document.createElement("strong");
          bold.textContent = part;
          paragraph.appendChild(bold);
        } else {
          paragraph.appendChild(document.createTextNode(part));
        }
      });

      bubble.appendChild(paragraph);
    });

  if (sources.length > 0) {
    const list = document.createElement("div");
    list.className = "sources";
    sources.forEach((title) => {
      const chip = document.createElement("em");
      chip.textContent = title;
      list.appendChild(chip);
    });
    bubble.appendChild(list);
  }

  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
}

function showTyping() {
  const wrapper = document.createElement("article");
  wrapper.className = "message bot";
  wrapper.id = "typingIndicator";

  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "⛰";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = '<span class="typing-dots"><i></i><i></i><i></i></span>';

  wrapper.appendChild(avatar);
  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
  const indicator = document.querySelector("#typingIndicator");
  if (indicator) indicator.remove();
}

function remember(role, content) {
  history.push({ role, content });
  if (history.length > MAX_HISTORY) history.shift();
}

function setBusy(busy) {
  input.disabled = busy;
  sendButton.disabled = busy;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    apiStatus.innerHTML = data.openai_configured
      ? '<span class="dot"></span>En linea'
      : '<span class="dot"></span>Modo demo (sin API key)';
    apiStatus.className = data.openai_configured ? "ready" : "missing";
  } catch (error) {
    apiStatus.innerHTML = '<span class="dot"></span>Sin conexion';
    apiStatus.className = "missing";
  }
}

async function askAgent(message) {
  addMessage(message, "user");
  input.value = "";
  setBusy(true);
  showTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history })
    });
    const data = await response.json();
    hideTyping();

    if (!response.ok) {
      addMessage(data.error || "Ocurrio un error consultando el agente.", "bot");
      return;
    }

    addMessage(data.answer, "bot", data.sources || []);
    remember("user", message);
    remember("assistant", data.answer);
  } catch (error) {
    hideTyping();
    addMessage(
      "No pude conectar con el servidor. Revisa que este activo e intenta de nuevo.",
      "bot"
    );
  } finally {
    setBusy(false);
    input.focus();
  }
}

function resetConversation() {
  history = [];
  messages.innerHTML = "";
  addMessage(WELCOME, "bot");
  input.focus();
}

prompts.forEach((prompt) => {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = prompt;
  button.addEventListener("click", () => askAgent(prompt));
  quickPrompts.appendChild(button);
});

document.querySelectorAll(".destination").forEach((card) => {
  card.addEventListener("click", () => {
    askAgent(card.dataset.question);
    card.blur();
  });
});

resetButton.addEventListener("click", resetConversation);

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (message) askAgent(message);
});

addMessage(WELCOME, "bot");
checkHealth();
