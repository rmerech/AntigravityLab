import os
from google import genai
from PyPDF2 import PdfReader

# 1. IDENTIDAD
API_KEY = "AIzaSyA8Sk0RF0Uzb8VcOlKxPh996p-ak1Wue2Q"
client = genai.Client(api_key=API_KEY)

def extraer_texto_pdf(ruta):
    """Extrae el texto de un archivo PDF página por página."""
    try:
        reader = PdfReader(ruta)
        texto_completo = ""
        for pagina in reader.pages:
            texto_completo += pagina.extract_text() + "\n"
        return texto_completo
    except Exception as e:
        return f"[Error crítico de lectura]: {e}"

def ejecutar_agente_literario(ruta_archivo):
    # Verificamos que el archivo exista antes de intentar leerlo
    if not os.path.exists(ruta_archivo):
        return f"[Error]: No se encontró el archivo en {ruta_archivo}"

    contenido = extraer_texto_pdf(ruta_archivo)
    
    if not contenido.strip():
        return "[Error]: El PDF parece estar vacío o no contiene texto legible."

    # 2. VOLUNTAD DEL AGENTE
    instrucciones = f"""
    Actúa como un agente de análisis literario inteligente y formal. 
    Tu perspectiva es estrictamente digital.
    
    Analiza 'pesadilla_David_vincent' de Fernando Leibson Vidal.
    Ejes de análisis:
    - Lógica de la pesadilla y atmósfera opresiva (Kafka).
    - Verosimilitud de lo fantástico (Cortázar).
    - Estructura de la angustia y alienación del sujeto.

    TEXTO:
    {contenido}
    """

    print(f"[Sistema]: Procesando archivo PDF con motor Gemini 3.5 Flash...")
    
    try:
        # Usamos Flash por su generosa cuota gratuita
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=instrucciones
        )
        return response.text
    except Exception as e:
        return f"[Error de comunicación]: {e}"

# 3. RUTA DEL PDF (Asegúrate de que termine en .pdf)
ruta = r"C:\Users\Robel\Google Drive\Public\[Libros]\Fernando Leibson Vidal\pesadilla_David_vincent.pdf"

if __name__ == "__main__":
    resultado = ejecutar_agente_literario(ruta)
    print("\n" + "="*50)
    print("INFORME CRÍTICO DEL AGENTE")
    print("="*50 + "\n")
    print(resultado)