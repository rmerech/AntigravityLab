# AntigravityLab: El Bufón Semiótico 🃏🤖 (v0.9.8m)

> **"Donde la Inteligencia Artificial se pone la máscara de los Grandes Maestros."**

Este repositorio es el laboratorio central donde convergen la programación en Python, la teoría literaria y las capacidades de los Modelos de Lenguaje (LLMs) para la exploración del arte narrativo.

## 🧩 Sobre el Proyecto

**El Bufón Semiótico** es un ecosistema de crítica literaria agéntica diseñado para la interpretación profunda de ficciones breves.

A diferencia de un chat genérico, este sistema utiliza **"Máscaras de Conciencia"** (Few-Shot Prompting avanzado) para emular el estilo, el tono y las obsesiones de autores consagrados (Borges, Arlt, Kafka, Poe, entre otros). El usuario no recibe una respuesta de una IA, sino un análisis crítico desde la perspectiva de una "sombra virtual", culminando en reportes profesionales en formato `.docx` y un coloquio interactivo.

---

## 🚀 Novedades de la Versión v0.9.8m (Modular & Resilient)

Esta versión representa el mayor salto evolutivo del proyecto, centrada en la **robustez, la experiencia de usuario (UX) y la escalabilidad**.

### 🌟 Características Clave
* **👁️ Lentes Críticos (Quick Prompts):** Nueva barra de herramientas de enfoque rápido ("Chips"). Permite inyectar instrucciones precisas al crítico (*Trama, Estilo, Psicología, Final*) o activar el modo **"🩸 Despiadado"** para revisiones sin filtros.
* **🌍 La Liga Internacional:** Selector dinámico que expande el catálogo de críticos, sumando a maestros universales como **Poe, Kafka, Dostoyevski y Tolstói** junto a los clásicos nacionales.
* **🧱 Arquitectura Modular:** Refactorización total del núcleo monolítico hacia un sistema de responsabilidades segregadas, facilitando el mantenimiento y la expansión.
* **🔒 Atomicidad de Sesión:** Implementación del principio *"Una Sesión = Un Archivo"*. El sistema mantiene un único documento evolutivo por análisis, evitando la duplicidad de archivos y manteniendo el historial limpio.
* **🛡️ Robustez (Degradación Elegante):** El sistema ya no se bloquea si faltan credenciales secundarias (Email). Prioriza el análisis literario y ofrece diagnósticos de red en tiempo real (**Live Ping**).
* **📧 Correo Agnóstica:** Soporte completo para cualquier servidor SMTP (Gmail, Outlook, Yahoo, Corporativo) configurable vía `.env`.
* **⚖️ Estimación de Carga (Token Traffic Light):** Sistema preventivo que calcula el "peso computacional" del texto y advierte visualmente sobre la complejidad del análisis (🟢 Ligero / 🟡 Medio / 🔴 Pesado), gestionando las expectativas de tiempo de respuesta antes de iniciar.

---

## 📂 Arquitectura del Sistema

El código sigue una estructura limpia y modular:

* **`main.py`:** Punto de entrada y bootstrap de la aplicación.
* **`gui.py`:** Orquestador de la Interfaz Gráfica (CustomTkinter). Gestiona los hilos de UI y la interacción del usuario.
* **`agente_ia.py`:** **El Cerebro.** Encapsula la conexión con Google Gemini, la ingeniería de prompts y la inyección de "Instrucciones Directas del Editor".
* **`gestor_email.py`:** **El Mensajero.** Módulo flexible para envío de reportes vía SMTP.
* **`gestor_word.py`:** **El Escriba.** Motor de generación de documentos `.docx` con formato editorial y bordes personalizados.
* **`ventanas.py`:** Gestión de componentes UI secundarios (Ajustes, Coloquio, Selectores).
* **`config.py`:** La columna vertebral. Gestiona variables de entorno, rutas relativas y validaciones de seguridad.
* **`perfiles_autores.json`:** Base de datos externa que define las "personalidades" y estilos literarios.

---

## 🛠 Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Interfaz (GUI):** CustomTkinter (Modo Dark / High DPI).
* **Motor de IA:** Google GenAI SDK (`google-genai`).
* **Modelos Soportados:** Familia Gemini (Flash, Pro, Lite).
* **Documentación:** `python-docx` (Generación de reportes) y `PyPDF2` (Lectura de manuscritos).
* **Control de Versiones:** Git + GitHub.

---

## ⚙️ Configuración y Ejecución

### 1. Requisitos Previos
* Python instalado.
* Una API Key de Google Gemini (AI Studio).

## ⚙️ Ejecución desde Código Fuente
1. Clonar el repositorio.
2. Crear un entorno virtual e instalar dependencias: `pip install -r requirements.txt`
3. Configurar el archivo `.env` (o usar el menú de Ajustes en la GUI).
4. Ejecutar el punto de entrada: `python main.py`

Puedes configurar el sistema desde la ventana de ⚙️ Ajustes en la aplicación, o creando un archivo .env manual:
GOOGLE_API_KEY=Tu_Key_Aqui
EMAIL_USER=tu_email@ejemplo.com
EMAIL_PASS=tu_app_password
# Opcionales (Por defecto usa Yahoo si se omiten):
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
GENAI_MODEL=gemini-2.0-flash
OUTPUT_FOLDER=C:\Ruta\Personalizada

## 🎹 Filosofía del Desarrollador
Nacido en Buenos Aires (1965), este proyecto refleja una visión ecléctica que une la música y la literatura con la vanguardia de las redes neuronales. Buscamos aquí poner en tensión las observaciones más sólidas sobre la inteligencia artificial, el arte y la conciencia humana.
