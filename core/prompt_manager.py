from core.imports import *
from langchain.prompts import PromptTemplate

class PromptManager:
    def __init__(self, user_prompt: str):
        """
        Maneja la plantilla del prompt proveniente del panel del usuario.
        No se usa ninguna plantilla por defecto.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("❌ No se ha definido un prompt en user/panel.py")

        self.template = user_prompt.strip()

    def build_prompt(self, rol: str, mensaje: str, historial: str):
        """
        Crea el prompt final que será enviado al modelo, 
        usando la plantilla definida por el usuario.
        """
        prompt = PromptTemplate(
            input_variables=["rol", "mensaje", "historial"],
            template=self.template
        )
        return prompt.format(rol=rol, mensaje=mensaje, historial=historial)
