# core/memory_manager.py
from core.imports import *

class MemoryManager:
    def __init__(self):
        self.usuarios = {}

    def get_memory(self, user_id: str):
        if user_id not in self.usuarios:
            self.usuarios[user_id] = ConversationBufferMemory(
                memory_key="historial", input_key="mensaje"
            )
        return self.usuarios[user_id]
