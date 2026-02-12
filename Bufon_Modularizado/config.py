import sys
import json
import os
import customtkinter as ctk
from dotenv import load_dotenv
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES - v0.9.8m
# ==============================================================================
# Hitos de esta versión:
# - Modularización: Refactorización mayor. División de gui.py en agente_ia.py y gestor_email.py.
# - Inteligencia: Implementación de Few-Shot Prompting.
# - Portabilidad: Gestión de rutas optimizada.
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
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.mail.yahoo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
MODELO_ACTUAL = os.getenv("GENAI_MODEL", "gemini-2.0-flash") # [NUEVO v0.9.7.1] Persistencia de modelo

# --- GESTIÓN ROBUSTA DE DIRECTORIOS (v0.9.7.7m) ---
# Intentamos usar la ruta del .env, pero validamos que sea segura.
_ruta_env = os.getenv("OUTPUT_FOLDER")
USANDO_FALLBACK = False
ESTADO_DIRECTORIO = "DESCONOCIDO"

if _ruta_env:
    _ruta_candidata = Path(_ruta_env)
    # Validaciones: Debe ser absoluta y el padre debe existir (o ser creable)
    # Nota: Para ser prácticos, si es absoluta intentamos usarla.
    # Si falla al crear o no tiene permisos, activaremos fallback.
    try:
        if not _ruta_candidata.is_absolute():
            raise ValueError("La ruta no es absoluta")
        
        if not _ruta_candidata.exists():
            _ruta_candidata.mkdir(parents=True, exist_ok=True)
            ESTADO_DIRECTORIO = "CREADO"
        else:
            ESTADO_DIRECTORIO = "EXISTENTE"
        
        # Prueba de escritura rápida
        _test_file = _ruta_candidata / ".write_test"
        with open(_test_file, 'w') as f:
            f.write("ok")
        os.remove(_test_file)
        
        DIRECTORIO_INFORMES = _ruta_candidata
    except Exception as e:
        print(f"[Sistema]: Ruta inválida en .env ({e}). Usando fallback.")
        USANDO_FALLBACK = True
        ESTADO_DIRECTORIO = "FALLBACK"
        DIRECTORIO_INFORMES = ruta_carpeta / "DataBufon"
else:
    USANDO_FALLBACK = True
    ESTADO_DIRECTORIO = "FALLBACK"
    DIRECTORIO_INFORMES = ruta_carpeta / "DataBufon"

# Aseguramos que el directorio final exista SÍ o SÍ inmediatamente
try:
    if not DIRECTORIO_INFORMES.exists():
         DIRECTORIO_INFORMES.mkdir(parents=True, exist_ok=True)
         if ESTADO_DIRECTORIO == "FALLBACK":
             # Si estamos en fallback y tuvimos que crear la carpeta local
             pass 
except Exception as e:
    print(f"[FATAL]: No se pudo crear directorio de informes: {e}")


# --- DICCIONARIO DE AUTORES (CRÍTICOS INVITADOS) ---
# --- DICCIONARIO DE AUTORES (CRÍTICOS INVITADOS) ---
ESTADO_CARGA_AUTORES = "OK"

def cargar_autores_desde_json():
    """Carga los perfiles de autores desde un archivo JSON externo."""
    global ESTADO_CARGA_AUTORES
    ruta_json = ruta_carpeta / "perfiles_autores.json"
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ALERTA]: No se encontró {ruta_json}. Usando diccionario vacío.")
        ESTADO_CARGA_AUTORES = "FALTANTE"
        return {}
    except json.JSONDecodeError:
        print(f"[ERROR]: Error de sintaxis en {ruta_json}.")
        ESTADO_CARGA_AUTORES = "ERROR_SINTAXIS"
        return {}

DICCIONARIO_AUTORES = cargar_autores_desde_json()
