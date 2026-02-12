import os
import json
from google import genai
from google.genai import types
from config import API_KEY, MODELO_ACTUAL, DICCIONARIO_AUTORES

# ==============================================================================
# MÓDULO AGENTE IA - v0.9.8m
# ==============================================================================

class AgenteIA:
    """
    Clase que encapsula toda la interacción con la API de Google Gemini.
    Ahora incluye la lógica de construcción de prompts y perfiles (v0.9.8m).
    """
    def __init__(self):
        self.client = None
        self.api_ready = False
        self._inicializar_cliente()

    def _inicializar_cliente(self):
        if API_KEY:
            try:
                self.client = genai.Client(api_key=API_KEY)
                self.api_ready = True
                print("[AgenteIA]: Cliente Gemini inicializado correctamente.")
            except Exception as e:
                print(f"[AgenteIA]: Error al inicializar cliente: {e}")
                self.api_ready = False
        else:
            print("[AgenteIA]: ADVERTENCIA - No se detectó API KEY.")
            self.api_ready = False

    def _construir_perfil(self, autor_nombre):
        """
        Construye el System Instruction a partir del nombre del autor usando DICCIONARIO_AUTORES.
        """
        datos_autor = DICCIONARIO_AUTORES.get(autor_nombre, {})
        
        if isinstance(datos_autor, dict):
            descripcion = datos_autor.get("descripcion", "Eres un asistente literario experto.")
            ejemplos = datos_autor.get("ejemplos_few_shot", [])
            
            perfil = descripcion
            if ejemplos:
                perfil += "\n\nEJEMPLOS DE ESTILO (FEW-SHOT):\n" + "\n".join([f"- {ex}" for ex in ejemplos])
            return perfil
        else:
            return str(datos_autor)

    def obtener_modelos_disponibles(self):
        """
        Obtiene la lista de modelos disponibles filtrando los no deseados.
        """
        try:
            if not self.api_ready: return []
            modelos_crudos = self.client.models.list()
            palabras_prohibidas = ["image", "audio", "tts", "robotics", "computer-use", "embedding", "vision"]
            lista_final = [m.name.replace("models/", "") for m in modelos_crudos if "gemini" in m.name.lower() and not any(p in m.name.lower() for p in palabras_prohibidas)]
            lista_final.sort(reverse=True)
            return lista_final
        except Exception as e:
            print(f"[AgenteIA Error Modelos]: {e}")
            return [
                "gemini-flash-lite-latest",
                "gemini-flash-latest",
                "gemini-3-flash-preview",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash"
            ]

    def procesar_analisis(self, texto_relato, autor_nombre, perspectiva_usuario=""):
        """
        Envía el texto del relato a Gemini para su análisis.
        Es un método bloqueante (síncrono).
        Recibe el nombre del autor y construye el perfil internamente.
        Retorna el diccionario JSON con el análisis.
        """
        if not self.api_ready:
            raise Exception("API Key no configurada o cliente no inicializado.")

        # Construcción del perfil dentro del Agente (Desacoplamiento)
        perfil_autor = self._construir_perfil(autor_nombre)

        prompt = (
            "IMPORTANTE: RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO. NO ESCRIBAS NADA FUERA DEL JSON.\n"
            "El JSON debe tener exactamente estas 4 claves:\n"
            "- 'titulos': [Lista de 3 títulos sugeridos]\n"
            "- 'sinopsis': 'Texto de la sinopsis'\n"
            "- 'conceptos': [Lista de 5 conceptos clave]\n"
            "- 'analisis_autor': 'Texto del análisis profundo según tu estilo personal'\n\n"
        )
        if perspectiva_usuario: 
            prompt += f"\nINSTRUCCIÓN DIRECTA DEL EDITOR: {perspectiva_usuario}. (IMPORTANTE: Prioriza esta instrucción sobre tu perfil habitual e intégrala en el análisis).\n"
        
        prompt_final = f"TEXTO A ANALIZAR:\n{texto_relato}\n\n{prompt}"

        import config
        modelo = config.MODELO_ACTUAL

        config_gen = types.GenerateContentConfig(
            system_instruction=perfil_autor, 
            response_mime_type="application/json"
        )
        
        try:
            print(f"[AgenteIA]: Enviando prompt a Gemini ({modelo})...")
            response = self.client.models.generate_content(
                model=modelo, 
                contents=prompt_final, 
                config=config_gen
            )
            print("[AgenteIA]: Respuesta recibida. Procesando JSON...")
            return json.loads(response.text)
        except Exception as e:
            raise e

    def iniciar_chat(self, autor_nombre):
        """
        Inicia una nueva sesión de chat con el perfil del autor.
        Recibe el nombre del autor y construye el perfil internamente.
        """
        if not self.api_ready:
            raise Exception("API Key no configurada.")
        
        perfil_autor = self._construir_perfil(autor_nombre)
        import config
        modelo = config.MODELO_ACTUAL
        
        try:
            chat_session = self.client.chats.create(
                model=modelo,
                config=types.GenerateContentConfig(
                    system_instruction=perfil_autor, 
                    temperature=0.7
                )
            )
            return chat_session
        except Exception as e:
            raise Exception(f"Error al crear sesión de chat: {e}")

    def enviar_mensaje(self, chat_session, mensaje):
        """
        Envía un mensaje a la sesión de chat existente.
        """
        try:
            response = chat_session.send_message(mensaje)
            return response.text if response and response.text else "[El autor permanece en silencio...]"
        except Exception as e:
            raise e

    def verificar_conexion(self):
        """
        Verifica la conectividad real con la API intentando listar 1 modelo.
        """
        try:
            if not self.api_ready: return False
            if not self.client: return False
            
            # Llamada simple sin parámetros para máxima compatibilidad
            # Iteramos el primer elemento para forzar la llamada de red
            for _ in self.client.models.list():
                break
            return True
        except Exception as e:
            print(f"[AgenteIA]: Falló verificación de conexión -> {e}")
            return False
