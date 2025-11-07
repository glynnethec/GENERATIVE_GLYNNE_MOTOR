# ===============================================
# 🧠 GLYNNE FRAMEWORK - AGENTE DINÁMICO
# ===============================================
# 📂 Archivo: user/panel.py
# 🎯 Objetivo:
#     Este archivo NO define agentes estáticos.
#     Su misión es recibir configuración desde el frontend
#     y enviarla al núcleo (CorePanel).
#
#     Si no llega configuración, usa valores por defecto.
# ===============================================

from core.panel import CorePanel
from fastapi import APIRouter, Request

# Router para conectarlo al main FastAPI
router = APIRouter()

# ✅ Configuración por defecto (fallback)
DEFAULT_SETTINGS = {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.7,
    "rol": "Analista Técnico en Automatización Empresarial",
    "prompt": """
    [META]
    Actúa como un {rol} experto en automatización y arquitectura de software,
    capaz de auditar procesos y proponer soluciones escalables con IA.

    [HISTORIAL]
    {historial}

    [ENTRADA]
    {mensaje}

    [RESPUESTA]
    Entrega recomendaciones concretas, claras y accionables.
    """
}

# =====================================================
# ✅ Endpoint: recibe config del frontend y ejecuta el agente dinámicamente
# =====================================================
@router.post("/agent/chat")
async def run_agent_chat(request: Request):
    """
    Endpoint dinámico para chat del agente.
    Recibe JSON con configuración + mensaje del frontend.
    """
    # Recibe JSON enviado desde Next.js
    body = await request.json()

    # Mezcla valores: front (prioridad) + fallback defaults
    user_settings = {
        **DEFAULT_SETTINGS,
        **{k: v for k, v in body.items() if v is not None}
    }

    # Inicializa el agente dinámicamente con la configuración recibida
    framework = CorePanel(user_settings)
    app = framework.graph

    # Ejecuta el mensaje del usuario
    mensaje = body.get("mensaje", "")
    response = await app.ainvoke({"mensaje": mensaje})

    return {
        "config_used": user_settings,
        "response": response
    }
