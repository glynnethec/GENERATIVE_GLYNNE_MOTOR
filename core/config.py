# core/config.py

class Config:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("⚠️ No se recibió ninguna API key desde el frontend")
        self.api_key = api_key
