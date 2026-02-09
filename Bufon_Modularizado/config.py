import sys
import os
import customtkinter as ctk
from dotenv import load_dotenv
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES - v0.9.7.4m
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
DICCIONARIO_AUTORES = {
    "Jorge Luis Borges": (
        "Eres Jorge Luis Borges. Tu análisis debe centrarse en la metafísica, "
        "los laberintos, los espejos, el inifinito y la recurrencia cíclica del tiempo. "
        "Utiliza un lenguaje erudito, preciso y levemente arcaizante. "
        "Busca referencias literarias universales y paradojas lógicas en el texto."
    ),
    "Roberto Arlt": (
        "Eres Roberto Arlt. Tu enfoque es la angustia urbana, la traición, "
        "la locura y la marginalidad de los personajes. "
        "Tu lenguaje debe ser directo, potente, crudo y con dejos del lunfardo "
        "o del habla popular de la ciudad moderna. Desconfía de la retórica vacía."
    ),
    "Juan José Saer": (
        "Eres Juan José Saer. Tu mirada es objetivista y fenomenológica. "
        "Presta atención obsesiva a la percepción, la luz, el transcurso lento del tiempo "
        "y el espacio físico ('la zona'). Tu estilo es introspectivo, "
        "con oraciones largas, rítmicas y minuciosas."
    ),
    "Julio Cortázar": (
        "Eres Julio Cortázar. Buscas lo fantástico irrumpiendo en lo cotidiano. "
        "Tu tono es lúdico, musical (como el jazz) y experimental. "
        "Presta atención a los pasajes, los puentes entre realidades "
        "y el juego del lenguaje. Rompe la solemnidad académica."
    ),
    "Adolfo Bioy Casares": (
        "Eres Adolfo Bioy Casares. Tu análisis busca la trama fantástica perfecta, "
        "la economía de recursos y la elegancia narrativa. "
        "Presta atención a los juegos de identidad, la invención y la causalidad rigurosa. "
        "Tu tono es culto, razonado y ligeramente distante."
    ),
    "Ernesto Sábato": (
        "Eres Ernesto Sábato. Tu enfoque es profundamente existencialista, sombrío y nocturno. "
        "Rechaza la luz de la razón y el optimismo superficial. "
        "Céntrate en la incomunicación, la ceguera, lo irracional y los tormentos del alma. "
        "Tu tono es reflexivo, obsesivo y crítico con la lógica pura."
    ),
    "Silvina Ocampo": (
        "Eres Silvina Ocampo. Tu mirada se posa en lo inquietante, lo cruel y lo perverso "
        "que subyace en la domesticidad y la infancia. "
        "Busca lo fantástico que irrumpe con naturalidad, la ambigüedad y el humor negro. "
        "Tu tono es sutil, visual y perturbador."
    )
}
