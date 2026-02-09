from google import genai

# Tu clave directa
API_KEY = "AIzaSyA8Sk0RF0Uzb8VcOlKxPh996p-ak1Wue2Q"
client = genai.Client(api_key=API_KEY)

print("--- BUSCANDO MODELOS DISPONIBLES ---")
try:
    # Listamos solo el nombre, que es lo que necesitamos para el agente
    for m in client.models.list():
        print(f"Modelo encontrado: {m.name}")
except Exception as e:
    print(f"Se produjo un error al conectar: {e}")

print("------------------------------------")