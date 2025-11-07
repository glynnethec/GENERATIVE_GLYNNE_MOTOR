# core/graph_manager.py
from core.imports import *
from core.memory_manager import MemoryManager
from typing import Any

class State(TypedDict):
    mensaje: str
    rol: str
    historial: str
    respuesta: str
    user_id: str


class GraphManager:
    """
    Gestiona el flujo principal del agente dentro del framework.
    Se conecta con el LLM, la memoria y el manejador de prompts.
    """

    def __init__(self, llm_manager, prompt_manager: 'PromptManager'):
        self.llm = llm_manager
        self.prompt_manager = prompt_manager
        self.memory = MemoryManager()

    def _to_str(self, value: Any) -> str:
        """
        Convierte cualquier tipo de respuesta a string para LangChain.
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, list):
            return " ".join(str(v) for v in value)
        elif isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        else:
            return str(value)

    def agente_node(self, state: State) -> State:
        """
        Nodo principal del grafo: procesa el mensaje del usuario,
        genera respuesta y guarda en memoria.
        """
        memory = self.memory.get_memory(state["user_id"])
        historial = memory.load_memory_variables({}).get("historial", "")

        prompt_text = self.prompt_manager.build_prompt(
            rol=state["rol"],
            mensaje=state["mensaje"],
            historial=historial
        )

        respuesta = self.llm.invoke(prompt_text)
        respuesta_str = self._to_str(respuesta)

        # ⚡ Guardamos como diccionario para LangChain
        memory.save_context({"mensaje": state["mensaje"]}, {"respuesta": respuesta_str})

        state["respuesta"] = respuesta_str
        state["historial"] = historial
        return state

    def build(self):
        """
        Crea y compila el grafo principal de LangGraph.
        """
        workflow = StateGraph(State)
        workflow.add_node("agente", self.agente_node)
        workflow.set_entry_point("agente")
        workflow.add_edge("agente", END)
        return workflow.compile()

    def compile_graph(self):
        """
        Alias de compatibilidad para versiones previas.
        """
        return self.build()
