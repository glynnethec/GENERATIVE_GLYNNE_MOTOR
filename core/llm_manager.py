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
        # Inicializa el LLM pasando modelo y temperatura explícitamente
        return ChatGroq(
            api_key=self.config.api_key,
            model=self.model_name,
            temperature=self.temperature
        )

    def invoke(self, prompt: str):
        """
        Llamada síncrona (para GraphManager)
        """
        return self.llm.invoke(prompt)

    async def ainvoke(self, prompt: str):
        """
        Llamada asíncrona (para LangGraph async)
        """
        return await self.llm.ainvoke(prompt)
