# core/llm_manager.py
from core.config import Config
from langchain_groq import ChatGroq

class LLMManager:
    def __init__(self, model="llama-3.3-70b-versatile", temperature=0.4, api_key: str = None):
        if not api_key:
            raise ValueError("⚠️ No se recibió ninguna API key desde el frontend")
        
        self.config = Config(api_key)
        self.model_name = model
        self.temperature = temperature
        self.llm = self._initialize_model()

    def _initialize_model(self):
        # Inicializa tu LLM real
        return ChatGroq(api_key=self.config.api_key)

    def invoke(self, prompt: str):
        """
        Método público para llamar al LLM, usado por GraphManager
        """
        return self.llm.invoke(prompt)
