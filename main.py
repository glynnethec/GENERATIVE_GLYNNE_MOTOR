from fastapi import FastAPI, Request, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from user.panel import router as dynamic_agent_router
from core.config import Config
from langchain_groq import ChatGroq
import uvicorn
import asyncio
from typing import List
from datetime import datetime
import json
import time
import platform
import psutil
import socket
import requests

# =====================================================
# 🧠 Cola Global de Logs (broadcast SSE)
# =====================================================
log_subscribers: List[asyncio.Queue] = []

def system_snapshot():
    """📊 Extrae info técnica del servidor sin exponer datos sensibles."""
    try:
        return {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "version": platform.release(),
            "cpu_cores": psutil.cpu_count(logical=True),
            "mem_used": round(psutil.virtual_memory().used / (1024**3), 2),
            "mem_total": round(psutil.virtual_memory().total / (1024**3), 2),
            "uptime": round(time.time() - psutil.boot_time(), 2),
        }
    except Exception:
        return {"info": "system data unavailable"}

def push_log(message: str, type: str = "info", details=None, elapsed: float = None, status: float = None):
    """Enviar log a todos los suscriptores SSE."""
    summary = None
    if details:
        summary = {
            "module": details.get("module", "core"),
            "model": details.get("model"),
            "role": details.get("rol"),
            "elapsed": round(elapsed, 3) if elapsed else None,
            "status": status,
        }

    log = {
        "time": datetime.utcnow().isoformat(),
        "msg": message,
        "type": type,
        "summary": summary,
        "details": details,
        "elapsed": elapsed,
        "status": status,
        "system": system_snapshot(),
    }

    for queue in list(log_subscribers):
        try:
            queue.put_nowait(log)
        except asyncio.QueueFull:
            pass

# =====================================================
# 📦 Legacy Model
# =====================================================
class MessageRequest(BaseModel):
    user_id: str
    rol: str
    mensaje: str

# =====================================================
# 🚀 Servidor GLYNNE
# =====================================================
class GlynneServer:
    def __init__(self):
        self.app = FastAPI(title="GLYNNE Agents API", version="2.0.0")

        # ✅ CORS para producción + vercel + local
        origins = [
            "https://glynneai.com",
            "https://www.glynneai.com",
            "https://glynne-sst-ai-hsiy.vercel.app",
            "http://localhost:3000",
            'https://glynne-fornt1.vercel.app'
        ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_core_routes()
        self.app.include_router(dynamic_agent_router, prefix="/dynamic", tags=["DynamicAgent"])
        push_log("GLYNNE Agents API Initialized ✅", "success", details={"module": "startup"})

    def _setup_core_routes(self):
        @self.app.get("/")
        async def home():
            push_log("Root endpoint hit", "info", details={"module": "root"})
            return {"message": "🚀 GLYNNE Agents API running (Dynamic Mode)"}

        # 🧠 Legacy chat endpoint
        @self.app.post("/chat")
        async def chat_legacy(req: MessageRequest):
            start = time.time()
            push_log(f"[Legacy Chat] Role={req.rol} | Message={req.mensaje}", "info", details={"module": "legacy-chat"})
            time.sleep(0.3)
            elapsed = time.time() - start
            push_log(
                "Processed legacy chat",
                "success",
                details={"module": "legacy-chat", "role": req.rol},
                elapsed=elapsed,
                status=1.0,
            )
            return {
                "warning": "Legacy /chat endpoint — usa /dynamic/agent/chat",
                "rol": req.rol,
                "mensaje": req.mensaje,
            }

        # 🔌 SSE Logs stream
        @self.app.get("/logs/stream")
        async def stream_logs(request: Request):
            push_log("Console attempting to connect via SSE 🔌", "info", details={"module": "logs"})
            queue: asyncio.Queue = asyncio.Queue()
            log_subscribers.append(queue)

            async def event_stream():
                try:
                    while True:
                        log = await queue.get()
                        yield f"data: {json.dumps(log)}\n\n"
                finally:
                    if queue in log_subscribers:
                        log_subscribers.remove(queue)
                    push_log("SSE client disconnected", "warn", details={"module": "logs"})

            return StreamingResponse(event_stream(), media_type="text/event-stream")

# =====================================================
# 🔑 Endpoint dinámico con API Key del usuario
# =====================================================
class DynamicChatRequest(BaseModel):
    api_key: str
    model: str
    temperature: float = 0.7
    rol: str
    prompt: str
    mensaje: str

def mount_user_key_endpoint(app: FastAPI):
    @app.post("/dynamic/agent/chat")
    async def dynamic_agent_chat(req: DynamicChatRequest):
        start = time.time()
        push_log(
            f"User requested /dynamic/agent/chat with key: {req.api_key[:4]}****",
            "info",
            details={"module": "dynamic-agent", "rol": req.rol},
        )
        try:
            config = Config(req.api_key)
            llm = ChatGroq(api_key=config.api_key, model="llama-3.3-70b-versatile")
            prompt_text = f"{req.prompt}\nRol: {req.rol}\nMensaje: {req.mensaje}"
            raw_response = llm.invoke(prompt_text)
            if raw_response is None:
                response = "❌ El agente no pudo generar respuesta"
            elif isinstance(raw_response, dict):
                response = json.dumps(raw_response)
            elif isinstance(raw_response, str):
                response = raw_response.strip()
            else:
                response = str(raw_response)
            if not response:
                response = "❌ El agente no pudo generar respuesta"

            elapsed = time.time() - start
            push_log(
                "LLM Response (preview)",
                "success",
                details={"module": "dynamic-agent", "model": "llama-3.3-70b-versatile", "rol": req.rol},
                elapsed=elapsed,
                status=1.0,
            )
            return {"reply": response}

        except Exception as e:
            elapsed = time.time() - start
            err_msg = str(e)
            if "invalid_api_key" in err_msg.lower() or "401" in err_msg:
                push_log(f"Invalid API key detected: {err_msg}", "error", details={"module": "dynamic-agent"}, elapsed=elapsed)
                return {"reply": "❌ API key inválida o error de autenticación"}

            push_log(f"Unexpected error: {err_msg}", "error", details={"module": "dynamic-agent"}, elapsed=elapsed)
            return {"reply": "❌ Error inesperado en la ejecución del agente"}

# ==============================================
# 🧠 Memoria persistente de agentes Full
# ==============================================
AGENT_MEMORY = {}  # Clave = agent_name, valor = lista de mensajes

# =====================================================
# 🧩 Endpoint extendido /dynamic/agent/chat/full
# =====================================================
class FullAgentChatRequest(BaseModel):
    agent_config: dict
    mensaje: str

def mount_full_agent_endpoint(app: FastAPI):
    @app.post("/dynamic/agent/chat/full")
    async def dynamic_agent_chat_full(req: FullAgentChatRequest = Body(...)):
        start = time.time()
        try:
            cfg = req.agent_config
            api_key = cfg.get("api_key")
            model = "llama-3.3-70b-versatile"
            rol = cfg.get("rol", "assistant")
            agent_name = cfg.get("agent_name", "default_agent")

            # Recuperar la memoria existente o inicializarla
            memory = AGENT_MEMORY.get(agent_name, [])

            # Construir contexto previo
            previous_context = "\n".join(memory) if memory else ""

            prompt = f"""
[META]
Actúa como un {rol}  no salgas de tu personage 

[AGENTE]
Nombre: {cfg.get("agent_name")}
Especialidad: {cfg.get("specialty")}
Objetivo: {cfg.get("objective")}
Proyecto: {cfg.get("business_info")}
Instrucciones: {cfg.get("additional_msg")}

[MEMORIA PREVIA]
{previous_context}

[ENTRADA]
{req.mensaje}

[RESPUESTA]
Entrega una respuesta breve, útil y directa.
            """

            push_log(
                f"[Dynamic Full] Received full agent config for role={rol}",
                "info",
                details={"module": "dynamic-agent-full", "rol": rol},
            )

            if not api_key:
                return {"reply": "❌ No se encontró API key en la configuración del agente."}

            config = Config(api_key)
            llm = ChatGroq(api_key=config.api_key, model=model)
            raw_response = llm.invoke(prompt)

            if raw_response is None:
                response = "❌ El agente no pudo generar respuesta"
            elif hasattr(raw_response, "content"):
                response = raw_response.content.strip()
            elif isinstance(raw_response, str):
                response = raw_response.strip()
            else:
                response = str(raw_response)

            # Guardar la interacción en la memoria
            memory.append(f"Usuario: {req.mensaje}")
            memory.append(f"{rol}: {response}")
            AGENT_MEMORY[agent_name] = memory  # actualizar memoria global

            elapsed = time.time() - start
            push_log(
                "LLM Response (Full Agent)",
                "success",
                details={"module": "dynamic-agent-full", "model": model, "rol": rol},
                elapsed=elapsed,
                status=1.0,
            )
            return {"reply": response}

        except Exception as e:
            elapsed = time.time() - start
            push_log(
                f"Error in /dynamic/agent/chat/full: {str(e)}",
                "error",
                details={"module": "dynamic-agent-full"},
                elapsed=elapsed,
            )
            return {"reply": f"❌ Error procesando agente completo: {str(e)}"}


# =====================================================
# 🟢 Endpoint para enviar mensajes a WhatsApp desde frontend
# =====================================================
class WhatsAppSendRequest(BaseModel):
    agent_config: dict
    mensaje: str
    whatsapp_token: str
    to_number: str

def mount_whatsapp_endpoint(app: FastAPI):
    @app.post("/dynamic/agent/chat/whatsapp")
    async def send_whatsapp_message(req: WhatsAppSendRequest):
        start = time.time()
        try:
            cfg = req.agent_config
            rol = cfg.get("rol", "assistant")
            agent_name = cfg.get("agent_name", "Agente")

            push_log(
                f"[WhatsApp] Recibido mensaje para enviar vía WA con rol={rol}",
                "info",
                details={"module": "whatsapp", "rol": rol},
            )

            prompt = f"""
[META]
Actúa como un {rol} y responde con máximo 100 palabras.

[AGENTE]
Nombre: {agent_name}
Especialidad: {cfg.get("specialty")}
Objetivo: {cfg.get("objective")}
Proyecto: {cfg.get("business_info")}
Instrucciones: {cfg.get("additional_msg")}

[ENTRADA]
{req.mensaje}

[RESPUESTA]
Entrega una respuesta breve, útil y directa.
            """

            config = Config(cfg.get("api_key", ""))
            llm = ChatGroq(api_key=config.api_key, model="llama-3.3-70b-versatile")
            raw_response = llm.invoke(prompt)

            if raw_response is None:
                response_text = "❌ El agente no pudo generar respuesta"
            elif hasattr(raw_response, "content"):
                response_text = raw_response.content.strip()
            elif isinstance(raw_response, str):
                response_text = raw_response.strip()
            else:
                response_text = str(raw_response)

            # Enviar mensaje a WhatsApp usando token del frontend
            whatsapp_api_url = f"https://graph.facebook.com/v17.0/me/messages"
            headers = {
                "Authorization": f"Bearer {req.whatsapp_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": req.to_number,
                "type": "text",
                "text": {"body": response_text},
            }

            wa_resp = requests.post(whatsapp_api_url, headers=headers, json=payload)
            wa_resp.raise_for_status()

            elapsed = time.time() - start
            push_log(
                f"[WhatsApp] Mensaje enviado exitosamente a {req.to_number}",
                "success",
                details={"module": "whatsapp", "rol": rol},
                elapsed=elapsed,
                status=1.0,
            )

            return {"reply": response_text, "whatsapp_status": wa_resp.json()}

        except requests.HTTPError as e:
            return {"reply": response_text, "whatsapp_status": f"❌ Error HTTP: {str(e)}"}
        except Exception as e:
            return {"reply": response_text, "whatsapp_status": f"❌ Error inesperado: {str(e)}"}

# =====================================================
# 🏁 Inicialización del servidor
# =====================================================
server = GlynneServer()
app = server.app

mount_user_key_endpoint(app)
mount_full_agent_endpoint(app)
mount_whatsapp_endpoint(app)

if __name__ == "__main__":
    push_log("Starting GLYNNE Server on port 8000...", "info", details={"module": "startup"})
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
