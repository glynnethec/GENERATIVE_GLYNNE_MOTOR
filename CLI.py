# main.py
from user.panel import app
import random
from core.memory_manager import MemoryManager

print("✅ Framework Glynne iniciado.")

memory = MemoryManager()
user_id = str(random.randint(10000, 90000))
rol = "auditor"

while True:
    user_input = input("Tu: ")
    if user_input.lower() == "salir":
        break
    result = app.invoke({"mensaje": user_input, "rol": rol, "historial": "", "user_id": user_id})
    print("IA:", result["respuesta"])
