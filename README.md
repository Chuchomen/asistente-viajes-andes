# Viajes Andes - Agente AI con Flask y OpenAI

Este proyecto resuelve el reto "El asistente que responde por tu negocio" con una app real en Python:

- Backend con Flask.
- Frontend tipo chat con memoria de conversacion.
- Base de conocimiento editable en `knowledge_base.json` (se recarga en cada pregunta, sin reiniciar Flask).
- Integracion con OpenAI usando la Responses API.
- El modelo recibe la base de conocimiento completa como unica fuente de verdad, asi entiende parafrasis ("me devuelven la plata si cancelo?") sin depender de palabras clave exactas.
- Respuesta segura cuando el agente no sabe algo: lo admite y deriva al WhatsApp de la agencia.
- Listo para publicar en Render con `gunicorn` y `render.yaml`.

## Estructura

```text
asistente-viajes-andes/
├── app.py
├── agent_core.py
├── knowledge_base.json
├── render.yaml
├── requirements.txt
├── .env.example
├── templates/
│   └── index.html
├── static/
│   ├── app.js
│   └── styles.css
└── tests/
    └── test_agent_core.py
```

## Como habilitar la API key de OpenAI

1. Entra a la plataforma de OpenAI y crea una API key.
2. Copia `.env.example` y renombralo como `.env`.
3. En `.env`, reemplaza `pon_aqui_tu_api_key` por tu clave real:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
FLASK_DEBUG=1
```

No subas el archivo `.env` a internet. Ese archivo es privado.

Nota: si estas en una red corporativa con proxy (error `CERTIFICATE_VERIFY_FAILED`),
el proyecto ya incluye `truststore`, que usa los certificados de Windows para
poder conectarse a OpenAI. No necesitas configurar nada extra.

## Como instalar y correr

Desde PowerShell:

```powershell
cd "D:\Proyectos Python\asistente-viajes-andes"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Luego abre:

```text
http://127.0.0.1:5000
```

## Como funciona el agente

1. El frontend envia la pregunta junto con los ultimos 8 mensajes de la conversacion.
2. El backend carga `knowledge_base.json` y arma un system prompt con TODA la base de conocimiento y las reglas de tono.
3. OpenAI responde solo con esa informacion; si el dato no existe, admite que no lo sabe y deriva al WhatsApp.
4. La busqueda por palabras clave (`retrieve_context`) se usa para mostrar las "Fuentes" de cada respuesta y como modo de respaldo cuando no hay API key configurada.

Gracias al historial, funcionan preguntas de seguimiento como:

> Usuario: Que incluye el plan a Peru?
> Usuario: y cuanto cuesta?

## Como entrenar el agente

Para este reto no necesitas fine-tuning. Lo correcto es "entrenarlo" alimentando su base de conocimiento:

1. Abre `knowledge_base.json`.
2. Agrega o edita datos concretos del negocio.
3. Incluye buenas palabras clave en `keywords` (se usan para las fuentes y el modo sin API key).
4. Guarda el archivo. No hace falta reiniciar Flask: se recarga en cada pregunta.

Ejemplo:

```json
{
  "id": "grupos",
  "category": "Reservas",
  "title": "Descuentos para grupos",
  "keywords": ["grupo", "grupos", "descuento", "empresa", "excursion"],
  "answer": "Para grupos de 10 o mas personas aplicamos tarifas especiales que se cotizan con un asesor."
}
```

Si no agregas ese dato, el agente debe responder que no sabe. Esa es una parte importante del reto.

Los paquetes internacionales (Cancun, Punta Cana, Europa, Japon) usan precios de
referencia tomados del mercado colombiano en julio de 2026 (Despegar, Viajes
Falabella, Viajes Exito y agencias especializadas), y cada respuesta aclara que
la cotizacion final la confirma un asesor. Ademas existe el dato "Destinos bajo
solicitud": si piden algo fuera del catalogo (cruceros, lunas de miel, otros
paises), el agente ofrece cotizarlo a la medida en vez de un simple "no se".

## Como publicar el link publico (Render, gratis)

El reto pide un link publico para que la comunidad lo pruebe. Con Render:

1. Sube el proyecto a un repositorio de GitHub (sin el archivo `.env`).
2. Entra a https://render.com y crea una cuenta (puedes usar tu cuenta de GitHub).
3. Clic en "New" > "Blueprint" y selecciona tu repositorio: Render detecta `render.yaml` automaticamente.
4. Cuando lo pida, escribe el valor de `OPENAI_API_KEY` (queda como variable de entorno secreta, nunca en el codigo).
5. Espera el deploy. Tu link queda como `https://andesbot.onrender.com` (o similar).

Nota: en el plan gratis el servidor se duerme tras 15 minutos sin uso; la primera respuesta despues de eso tarda ~30 segundos.

## Preguntas de prueba

- Cuanto cuesta el plan a Cartagena?
- Que incluye el plan a Peru? / y cuanto cuesta?
- Cuanto cuesta un viaje a Japon?
- Puedo pagar con Nequi?
- Me devuelven la plata si cancelo?
- Tienen cruceros? (fuera de catalogo: debe ofrecer cotizacion a la medida)
- Hay descuentos para grupos? (no esta en la base: debe admitir que no sabe)

## Texto sugerido para Platzi

Hola comunidad. Mi proyecto es AndesBot, un agente AI para Viajes Andes, una agencia de viajes boutique con destinos nacionales e internacionales. Lo construi con Python, Flask y la API de OpenAI (sin plantillas): el agente tiene una base de conocimiento editable con 20 datos del negocio (paquetes nacionales e internacionales con precios basados en referencias reales del mercado colombiano, pagos, reservas, cambios, cancelaciones, documentos, seguros y horarios) que se inyecta completa al modelo como unica fuente de verdad. Tiene memoria de conversacion para preguntas de seguimiento y, si le preguntas algo que no esta en su base, no inventa: admite que no lo sabe y deriva al WhatsApp de la agencia. Pruebenlo aqui: [TU LINK DE RENDER]
