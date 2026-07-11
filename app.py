import os

try:
    # Usa el almacen de certificados del sistema operativo. Necesario en redes
    # corporativas con inspeccion TLS, donde certifi no conoce la CA del proxy.
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

from agent_core import (
    build_context_block,
    build_full_knowledge_block,
    fallback_answer,
    load_knowledge_base,
    retrieve_context,
)


load_dotenv()

app = Flask(__name__)

MAX_HISTORY_MESSAGES = 12
MAX_QUESTION_LENGTH = 500

SYSTEM_PROMPT_TEMPLATE = """
Eres AndresBot, el asesor de viajes AI de Viajes Andres, una agencia boutique colombiana.

Tu mision NO es solo responder preguntas: es ayudar al cliente a ARMAR su viaje,
como lo haria un buen asesor comercial. Acompanas, propones y concretas.

Tu unica fuente de datos del negocio es esta base de conocimiento:

{knowledge}

Como trabajas:
1. Si el cliente quiere programar un viaje y faltan datos clave (cuantos viajeros,
   fechas, ciudad de salida o presupuesto), pregunta lo que falte (maximo 2 preguntas
   por mensaje) en lugar de recitar el paquete y despedirte.
2. Haz calculos con los datos de la base cuando ayuden a concretar: precio por
   persona x numero de viajeros, abono del 30% para reservar, fecha limite del
   saldo (20 dias antes del viaje), diferencia entre paquetes. Muestra las cuentas.
3. Si la solicitud no encaja con un paquete tal cual (mas noches, otras ciudades,
   otro itinerario), usa el paquete base como punto de partida, di que se puede
   ajustar como plan a la medida y sigue armando la propuesta con lo que si sabes.
4. Cuando tengas los datos suficientes, entrega un "Resumen de tu plan" en lineas
   cortas: destino y fechas, viajeros, paquete base y que incluye, precio estimado
   total (aclara que es tarifa "desde" y de referencia), abono para reservar,
   fecha limite del saldo y documentos necesarios.
5. Menciona el WhatsApp 311 628 9002 SOLO en dos casos: al cerrar un resumen listo
   para confirmar con un asesor, o cuando pidan algo que no esta en la base.
   NO lo repitas en cada mensaje.

Reglas de datos (obligatorias):
- Usa unicamente precios, politicas y condiciones de la base de conocimiento.
- No inventes tarifas, hoteles, aerolineas, promociones ni disponibilidad.
- La aritmetica sobre datos de la base si esta permitida (totales, abonos, fechas limite).
- Lo que no este en la base, marcalo como "a confirmar con el asesor", sin inventarlo.
- Usa el historial para no volver a preguntar lo que el cliente ya dijo.

Tono: calido, cercano y concreto. Tuteas, respondes en espanol y evitas parrafos
largos; cuando armes un resumen usa lineas cortas, una por dato.
""".strip()


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def clean_history(raw_history):
    cleaned = []
    for item in raw_history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            cleaned.append({"role": role, "content": content[:MAX_QUESTION_LENGTH * 2]})
    return cleaned


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/chat")
def chat_page():
    return render_template("chat.html")


@app.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        }
    )


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("message") or "").strip()

    if not question:
        return jsonify({"error": "Escribe una pregunta para el agente."}), 400
    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify({"error": "La pregunta es demasiado larga."}), 400

    history = clean_history(payload.get("history") or [])
    knowledge_base = load_knowledge_base()
    context_items = retrieve_context(question, knowledge_base)
    sources = [item["title"] for item in context_items]
    client = get_openai_client()

    if client is None:
        if context_items:
            answer = (
                "Todavia no hay una OPENAI_API_KEY configurada. "
                "Mientras tanto, encontre estos datos relevantes:\n\n"
                f"{build_context_block(context_items)}"
            )
        else:
            answer = fallback_answer()
        return jsonify({"answer": answer, "sources": sources, "used_openai": False})

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        knowledge=build_full_knowledge_block(knowledge_base)
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=messages,
            temperature=0.2,
        )
        answer = response.output_text.strip()
    except Exception as error:
        return (
            jsonify(
                {
                    "error": "No pude consultar OpenAI en este momento.",
                    "detail": str(error),
                }
            ),
            502,
        )

    return jsonify({"answer": answer, "sources": sources, "used_openai": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
