# core/panel.py
from core.imports import *
from core.llm_manager import LLMManager
from core.memory_manager import MemoryManager
from core.prompt_manager import PromptManager
from core.graph_manager import GraphManager


class CorePanel:
    """
    Ensambla el framework a partir de la configuración del usuario.
    El usuario pasa su configuración desde user/panel.py
    """

    def __init__(self, user_settings: dict):
        self.user_settings = user_settings

        # Configuración inicial del modelo y parámetros
        self.model = user_settings.get("model", "Llama-3.1-8B-Instant")
        self.temperature = user_settings.get("temperature", 0.5)
        self.prompt_text = user_settings.get("prompt", "")
        self.rol = user_settings.get("rol", "auditor")

        # ==========================
        # Inicializar componentes Core
        # ==========================
        self.llm_manager = LLMManager(
            model=self.model, 
            temperature=self.temperature, 
            api_key=user_settings.get("api_key")  # <-- PASA la API key recibida desde frontend
        )

        self.memory_manager = MemoryManager()
        self.prompt_manager = PromptManager(self.prompt_text)
        self.graph_manager = GraphManager(self.llm_manager, self.prompt_manager)

        # ==========================
        # Construcción del flujo LangGraph
        # ==========================
        # Se usa .build(), y se incluye un alias interno para compatibilidad futura
        if hasattr(self.graph_manager, "build"):
            self.graph = self.graph_manager.build()
        else:
            # Alias en caso de versiones previas
            self.graph = self.graph_manager.compile_graph()

        print(f"✅ Framework Glynne configurado con modelo: {self.model} | Temp: {self.temperature}")

    def update_settings(self, new_settings: dict):
        """
        Permite cambiar dinámicamente configuraciones desde runtime.
        """
        self.user_settings.update(new_settings)
        self.__init__(self.user_settings)
