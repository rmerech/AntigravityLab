import sys
import json
import os
import customtkinter as ctk
from dotenv import load_dotenv
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES - v0.9.7.6m
# ==============================================================================
# Hitos de esta versión:
# - Modularización: Migración de perfiles críticos a 'perfiles_autores.json'.
# - Inteligencia: Implementación de Few-Shot Prompting (Arlt, Sábato, Borges, etc.).
# - Portabilidad: Gestión de rutas optimizada para 'Maria DELLicia' (Notebook) 
#   y 'The Specimen' (Studio) vía Google Drive.
# - Infraestructura: Integración validada con Docker y MCP GitHub Server.
# ==============================================================================

# Configuración global de CustomTkinter
ctk.set_appearance_mode("Dark")        # Tema oscuro (Dark) o claro (Light)
ctk.set_default_color_theme("blue")    # Acento de color principal (azul)

# Carga de variables de entorno (.env)
# Detección de ruta (Compatible con PyInstaller y Script normal)
if getattr(sys, 'frozen', False):
    # Si es un .exe, buscamos la ruta del ejecutable
    ruta_carpeta = Path(sys.executable).parent
else:
    # Si es un script .py, buscamos la ruta del archivo actual
    ruta_carpeta = Path(__file__).resolve().parent

load_dotenv(ruta_carpeta / ".env")

# Obtención de credenciales
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
MAIL_USER = os.getenv("EMAIL_USER")
MAIL_PASS = os.getenv("EMAIL_PASS")
MODELO_ACTUAL = os.getenv("GENAI_MODEL", "gemini-2.0-flash") # [NUEVO v0.9.7.1] Persistencia de modelo
DIRECTORIO_INFORMES = os.getenv("OUTPUT_FOLDER")
if not DIRECTORIO_INFORMES:
    DIRECTORIO_INFORMES = ruta_carpeta / "DataBufon"
else:
    DIRECTORIO_INFORMES = Path(DIRECTORIO_INFORMES)

# --- DICCIONARIO DE AUTORES (CRÍTICOS INVITADOS) ---
# --- DICCIONARIO DE AUTORES (CRÍTICOS INVITADOS) ---
def cargar_autores_desde_json():
    """Carga los perfiles de autores desde un archivo JSON externo."""
    ruta_json = ruta_carpeta / "perfiles_autores.json"
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ALERTA]: No se encontró {ruta_json}. Usando diccionario vacío.")
        return {}
    except json.JSONDecodeError:
        print(f"[ERROR]: Error de sintaxis en {ruta_json}.")
        return {}

DICCIONARIO_AUTORES = cargar_autores_desde_json()
