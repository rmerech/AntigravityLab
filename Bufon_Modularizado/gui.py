import sys
import os
import customtkinter as ctk
import threading
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google import genai
from google.genai import types
from PyPDF2 import PdfReader
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

# Importaciones de módulos locales
from config import API_KEY, MAIL_USER, MAIL_PASS, MODELO_ACTUAL, DICCIONARIO_AUTORES, DIRECTORIO_INFORMES, USANDO_FALLBACK, ESTADO_DIRECTORIO
from utils import ToolTip, limpiar_texto
from gestor_word import GestorWord

# ==============================================================================
# INTERFAZ GRÁFICA - v0.9.7.4m
# ==============================================================================

class ElBufonSemiotico(ctk.CTk):
    """
    Clase principal de la interfaz. Versión v0.9.7.4m (Arquitectura Modular).
    """
    def __init__(self):
        super().__init__()

        # --- CONFIGURACIÓN BÁSICA DE LA VENTANA ---
        self.title("EL BUFÓN SEMIÓTICO v0.9.7.6m (Arquitectura Modular)")
        self.geometry("1100x650")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Variables de estado
        self.ruta_archivo_pdf = ""
        self.ruta_ultimo_word = ""
        self.api_ready = bool(API_KEY)
        # Definición de ruta base compatible con .exe
        if getattr(sys, 'frozen', False):
            self.ruta_base = Path(sys.executable).parent
        else:
            self.ruta_base = Path(__file__).resolve().parent

        # Variables para Coloquio
        self.historial_coloquio = []
        self.chat_session = None
        self.ventana_coloquio = None
        self.autor_actual = ""
        self.perfil_autor_actual = ""
        self.datos_json_actual = {}
        
        # Flag para evitar guardado redundante
        self.reporte_actual_guardado = False

        # --- BARRA LATERAL (SIDEBAR) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        # Logo y Versión
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="EL BUFÓN\nSEMIÓTICO", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 0))
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text="v0.9.7.5m", font=ctk.CTkFont(size=10), text_color="gray")
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Botón Cargar
        self.btn_cargar = ctk.CTkButton(self.sidebar_frame, text="CARGAR RELATO", command=self.seleccionar_archivo)
        self.btn_cargar.grid(row=2, column=0, padx=20, pady=10)

        # Selector Crítico
        self.lbl_critico = ctk.CTkLabel(self.sidebar_frame, text="CRÍTICO INVITADO:", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_critico.grid(row=3, column=0, padx=20, pady=(15, 5))
        autores_lista = list(DICCIONARIO_AUTORES.keys())
        self.option_autor = ctk.CTkOptionMenu(self.sidebar_frame, values=autores_lista)
        if autores_lista: self.option_autor.set(autores_lista[0])
        self.option_autor.grid(row=4, column=0, padx=20, pady=(0, 10))

        # Opciones
        self.lbl_opciones = ctk.CTkLabel(self.sidebar_frame, text="OPCIONES DE ANÁLISIS:", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_opciones.grid(row=5, column=0, padx=20, pady=(15, 5))

        self.titulos_var = ctk.BooleanVar(value=True)
        self.sinopsis_var = ctk.BooleanVar(value=True)
        self.conceptos_var = ctk.BooleanVar(value=True)

        chk_font = ctk.CTkFont(size=12)
        self.chk_1 = ctk.CTkCheckBox(self.sidebar_frame, text="Títulos Alternativos", variable=self.titulos_var, 
                                     font=chk_font, checkbox_width=18, checkbox_height=18, corner_radius=4)
        self.chk_1.grid(row=6, column=0, padx=20, pady=(5, 0), sticky="w")
        self.chk_2 = ctk.CTkCheckBox(self.sidebar_frame, text="Sinopsis", variable=self.sinopsis_var,
                                     font=chk_font, checkbox_width=18, checkbox_height=18, corner_radius=4)
        self.chk_2.grid(row=7, column=0, padx=20, pady=(5, 0), sticky="w")
        self.chk_3 = ctk.CTkCheckBox(self.sidebar_frame, text="Conceptos Clave", variable=self.conceptos_var,
                                     font=chk_font, checkbox_width=18, checkbox_height=18, corner_radius=4)
        self.chk_3.grid(row=8, column=0, padx=20, pady=(5, 0), sticky="w")

        # Apariencia
        self.lbl_apariencia = ctk.CTkLabel(self.sidebar_frame, text="Apariencia:", anchor="w")
        self.lbl_apariencia.grid(row=10, column=0, padx=20, pady=(10, 0))
        self.option_apariencia = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                   command=self.cambiar_apariencia)
        self.option_apariencia.grid(row=11, column=0, padx=20, pady=(10, 10))

        # Status y Ajustes
        self.status_indicator = ctk.CTkLabel(self.sidebar_frame, text="...", font=ctk.CTkFont(size=10, weight="bold"))
        self.status_indicator.grid(row=12, column=0, padx=20, pady=(10, 0))

        # Indicador de Modelo
        self.lbl_modelo_actual_ui = ctk.CTkLabel(self.sidebar_frame, text=f"Modelo: {MODELO_ACTUAL}", 
                                                 font=ctk.CTkFont(size=10), text_color="gray")
        self.lbl_modelo_actual_ui.grid(row=13, column=0, padx=20, pady=(0, 5))

        self.btn_ajustes = ctk.CTkButton(self.sidebar_frame, text="⚙️ Ajustes", 
                                         fg_color="transparent", border_width=1, 
                                         text_color=("gray10", "#DCE4EE"), border_color=("gray10", "#DCE4EE"),
                                         command=self.abrir_ajustes)
        self.btn_ajustes.grid(row=14, column=0, padx=20, pady=(5, 20))
        ToolTip(self.btn_ajustes, "Accede a las opciones de configuración del agente, email del remitente y api keys indispensables")


        # --- ÁREA PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.entry_perspectiva = ctk.CTkEntry(self.header_frame, placeholder_text="OPCIONAL: Nota adicional para el Crítico...", height=35)
        self.entry_perspectiva.pack(fill="x", pady=(0, 10))
        self.entry_perspectiva.insert(0, "Enfatiza el uso del tiempo.")
        ToolTip(self.entry_perspectiva, "OPCIONAL: Instrucciones específicas que se anexarán al pedido")

        self.entry_emails = ctk.CTkEntry(self.header_frame, placeholder_text="Correos colaboradores (separados por coma)...", height=35)
        self.entry_emails.pack(fill="x")
        ToolTip(self.entry_emails, "Ingrese las direcciones de correo separadas por coma para enviar el reporte automáticamente.")
        self.entry_emails.bind("<KeyRelease>", self._validar_email_input)

        # Info Archivo
        self.info_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=30)
        self.info_frame.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.lbl_archivo = ctk.CTkLabel(self.info_frame, text="Archivo: Ninguno", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_archivo.pack(side="left")

        # Barra de Progreso
        self.progressbar = ctk.CTkProgressBar(self.main_frame)
        self.progressbar.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.progressbar.set(0)
        self.progressbar.grid_remove()

        # TextBox
        self.textbox = ctk.CTkTextbox(self.main_frame, font=("Consolas", 12), wrap="word") 
        self.textbox.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        try:
            self.textbox._textbox.tag_config("system_msg", foreground="#00FF00", font=("Courier New", 10))
            self.textbox._textbox.tag_config("warning_msg", foreground="#FF5555", font=("Courier New", 10, "bold"))
        except Exception:
            pass

        self._escribir_seguro(self.textbox, "--- El sistema espera su consulta ---\n", modo="overwrite")
        
        if ESTADO_DIRECTORIO == "FALLBACK":
            msg_alerta = f"[ALERTA RUTA]: La ruta del .env falló. Se usará la carpeta local 'DataBufon'.\n"
            msg_alerta += f"Ruta activa: {DIRECTORIO_INFORMES}\n"
            self._escribir_seguro(self.textbox, msg_alerta)
        elif ESTADO_DIRECTORIO == "CREADO":
            msg_alerta = f"\n[AVISO SISTEMA]: La carpeta de destino no existía. Se ha creado automáticamente en: \n ----->> {DIRECTORIO_INFORMES} Puede cambiarla en AJUSTES\n"
            self._escribir_seguro(self.textbox, msg_alerta)
        else:
            # Caso EXISTENTE (o cualquier otro): Mostrar ruta activa informativa
            self._escribir_seguro(self.textbox, f"\n[System]: Ruta de informes actual: {DIRECTORIO_INFORMES}\n")

        # Botones Acciones
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")

        self.btn_ejecutar = ctk.CTkButton(self.action_frame, text="INICIAR ANÁLISIS", 
                                          command=self.ejecutar_agente, 
                                          state="disabled", fg_color="#1F538D", height=40)
        self.btn_ejecutar.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.btn_enviar = ctk.CTkButton(self.action_frame, text="MAIL A COLABORADORES", 
                                         command=self.enviar_reporte_email, 
                                         state="disabled", fg_color="#2E7D32", height=40)
        self.btn_enviar.pack(side="left", expand=True, fill="x", padx=10)

        self.btn_reset = ctk.CTkButton(self.action_frame, text="NUEVA CONSULTA", 
                                        command=self.limpiar_interfaz, 
                                        fg_color="#444", hover_color="#333", height=40)
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=(10, 0))

        # Botón para Coloquio
        self.btn_conversar = ctk.CTkButton(self.main_frame, text="CONVERSAR CON EL AUTOR",
                                            command=self.abrir_coloquio,
                                            state="disabled", fg_color="#5C3A93", height=35)
        self.btn_conversar.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.btn_conversar.grid_remove() # Oculto al inicio

        # Inicialización del cliente genai
        self._inicializar_cliente()
        self.verificar_estado_sistema()

    def _inicializar_cliente(self):
        if self.api_ready:
            self.client = genai.Client(api_key=API_KEY)
            print("[Terminal]: Cliente Gemini inicializado correctamente.")
        else:
            print("[Terminal]: ADVERTENCIA - No se detectó API KEY.")
            self._escribir_seguro(self.textbox, "\n[ALERTA]: No se detectó API KEY de Gemini. Revise su archivo .env.\n")

    def _escribir_seguro(self, widget, texto, modo="append"):
        try:
            widget.configure(state="normal")
            
            tags_to_apply = ()
            if texto.lstrip().startswith(("[ALERTA RUTA]", "[AVISO SISTEMA]", "[AVISO_RUTA]", "[FALLBACK]")):
                 tags_to_apply = ("warning_msg",)
            elif texto.lstrip().startswith(("[System]", "[Terminal]", "[ALERTA]")):
                 tags_to_apply = ("system_msg",)
            
            start_index = widget.index("insert")
            if modo == "overwrite":
                widget.delete("0.0", "end")
                start_index = "0.0"
            elif modo == "insert_start":
                start_index = "0.0"
            else:
                 start_index = widget.index("end-1c")

            if modo == "overwrite":
                widget.insert("0.0", texto)
            elif modo == "insert_start":
                widget.insert("0.0", texto)
            else: # append
                widget.insert("end", texto)
            
            if tags_to_apply:
                try:
                     count = len(texto)
                     widget._textbox.tag_add("system_msg", start_index, f"{start_index}+{count}c")
                except:
                     pass

            widget.see("end" if modo == "append" else "0.0")
            widget.configure(state="disabled")
        except Exception as e:
            print(f"[UI Error]: Falló escritura segura -> {e}")

    def verificar_estado_sistema(self):
        k1 = os.getenv("GOOGLE_API_KEY")
        k2 = os.getenv("EMAIL_USER")
        k3 = os.getenv("EMAIL_PASS")

        if k1 and k2 and k3:
            self.status_indicator.configure(text="● SISTEMA LISTO", text_color="#4CAF50")
            if self.ruta_archivo_pdf:
                self.btn_ejecutar.configure(state="normal")
            self.api_ready = True
            
            contenido_actual = self.textbox.get("1.0", "end")
            if "[ALERTA]" in contenido_actual:
                 self._escribir_seguro(self.textbox, "--- El sistema espera su consulta ---\n", modo="overwrite")
        else:
            self.status_indicator.configure(text="○ CONFIGURACIÓN PENDIENTE", text_color="#FFA000")
            self.btn_ejecutar.configure(state="disabled")
            self.api_ready = False
            self._escribir_seguro(self.textbox, "\n[ALERTA]: Faltan configuraciones. Use el botón '⚙️ Ajustes'.\n")

    def abrir_ajustes(self):
        toplevel = ctk.CTkToplevel(self)
        toplevel.title("Ajustes del Sistema")
        ancho = 420
        alto = 550
        x = self.winfo_x() + (self.winfo_width() // 2) - (ancho // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (alto // 2)
        toplevel.geometry(f"{ancho}x{alto}+{x}+{y}")
        toplevel.attributes("-topmost", True)
        
        frame = ctk.CTkFrame(toplevel)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Configuración de Credenciales", font=("Arial", 14, "bold")).pack(pady=(0, 15))

        ctk.CTkLabel(frame, text="Google Gemini API Key:").pack(anchor="w")
        entry_api = ctk.CTkEntry(frame, width=300)
        entry_api.pack(pady=(0, 10))
        entry_api.insert(0, os.getenv("GOOGLE_API_KEY", ""))

        ctk.CTkLabel(frame, text="Email User (Gmail/Yahoo):").pack(anchor="w")
        entry_user = ctk.CTkEntry(frame, width=300)
        entry_user.pack(pady=(0, 10))
        entry_user.insert(0, os.getenv("EMAIL_USER", ""))

        ctk.CTkLabel(frame, text="Email Password (App Password):").pack(anchor="w")
        frame_pass = ctk.CTkFrame(frame, fg_color="transparent")
        frame_pass.pack(fill="x", pady=(0, 15))
        entry_pass = ctk.CTkEntry(frame_pass, width=260, show="*")
        entry_pass.pack(side="left", fill="x", expand=True)
        entry_pass.insert(0, os.getenv("EMAIL_PASS", ""))

        def toggle_pass():
            if entry_pass.cget("show") == "*":
                entry_pass.configure(show="")
                btn_eye.configure(text="🔒")
            else:
                entry_pass.configure(show="*")
                btn_eye.configure(text="👁")

        btn_eye = ctk.CTkButton(frame_pass, text="👁", width=35, command=toggle_pass, fg_color="#555", hover_color="#444")
        btn_eye.pack(side="right", padx=(5, 0))

        def guardar():
            v_api, v_user, v_pass = entry_api.get().strip(), entry_user.get().strip(), entry_pass.get().strip()
            
            # Obtener estado actual de configuración para no perderlo
            import config
            v_model = config.MODELO_ACTUAL
            v_folder = str(config.DIRECTORIO_INFORMES)
            
            try:
                env_path = self.ruta_base / ".env"
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f"GOOGLE_API_KEY={v_api}\n")
                    f.write(f"EMAIL_USER={v_user}\n")
                    f.write(f"EMAIL_PASS={v_pass}\n")
                    f.write(f"GENAI_MODEL={v_model}\n")
                    f.write(f"OUTPUT_FOLDER={v_folder}\n")
                
                # Actualizar entorno
                actualizaciones = {
                    "GOOGLE_API_KEY": v_api,
                    "EMAIL_USER": v_user,
                    "EMAIL_PASS": v_pass,
                    "GENAI_MODEL": v_model,
                    "OUTPUT_FOLDER": v_folder
                }
                os.environ.update(actualizaciones)
                self._inicializar_cliente()
                self.verificar_estado_sistema()
                toplevel.destroy()
                messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

        # --- NUEVA SECCIÓN: DIRECTORIO DE INFORMES ---
        ctk.CTkLabel(frame, text="Directorio de Informes:", font=("Arial", 10, "bold")).pack(anchor="center", pady=(10, 0))
        
        # Import local para asegurar acceso a config actualizado
        import config
        lbl_dir = ctk.CTkLabel(frame, text=str(config.DIRECTORIO_INFORMES), font=("Arial", 9), text_color="gray", wraplength=380, justify="center")
        lbl_dir.pack(pady=(0, 5), anchor="center")

        def seleccionar_carpeta():
            toplevel.attributes("-topmost", False)
            ruta_elegida = filedialog.askdirectory()
            toplevel.attributes("-topmost", True)
            toplevel.lift()
            if ruta_elegida:
                ruta_final = Path(ruta_elegida) / "DataBufon"
                ruta_final.mkdir(parents=True, exist_ok=True)
                
                config.DIRECTORIO_INFORMES = ruta_final
                lbl_dir.configure(text=str(ruta_final))
                
                # Guardar en .env inmediatamente
                try:
                    env_path = self.ruta_base / ".env"
                    lines = open(env_path).readlines() if env_path.exists() else []
                    with open(env_path, "w", encoding="utf-8") as f:
                        found = False
                        ruta_str = str(ruta_final)
                        for l in lines:
                            if l.startswith("OUTPUT_FOLDER="):
                                f.write(f"OUTPUT_FOLDER={ruta_str}\n")
                                found = True
                            else:
                                f.write(l)
                        if not found:
                            f.write(f"OUTPUT_FOLDER={ruta_str}\n")
                    os.environ["OUTPUT_FOLDER"] = ruta_str
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo guardar ruta: {e}")

        # --- BOTONES EN PARALELO (GRID) ---
        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=(5, 10))

        btn_selec = ctk.CTkButton(frame_botones, text="SELECCIONAR CARPETA", fg_color="#555", hover_color="#444", 
                      command=seleccionar_carpeta)
        btn_selec.pack(side="left", expand=True, fill="x", padx=5)
        ToolTip(btn_selec, "Carpeta en la que se guardará el material generado")

        ctk.CTkButton(frame_botones, text="SELECCIONAR MODELO IA", fg_color="#1F538D", 
                      command=lambda: [toplevel.destroy(), self.abrir_selector_modelo()]).pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(frame, text="GUARDAR CONF", fg_color="#2E7D32", command=guardar).pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text="El Bufón Semiótico: Una perla dentro de un diamante literario.\nUn proyecto co-creado entre Robel y Gemini", font=("Arial", 9, "italic"), text_color="gray").pack(pady=(10, 0))

    def cambiar_apariencia(self, nuevo_modo):
        ctk.set_appearance_mode(nuevo_modo)

    def obtener_modelos_disponibles(self):
        try:
            if not self.api_ready: return []
            if not hasattr(self, 'client'): raise Exception("Cliente no inicializado")

            modelos_crudos = self.client.models.list()
            palabras_prohibidas = ["image", "audio", "tts", "robotics", "computer-use", "embedding", "vision"]
            lista_final = [m.name.replace("models/", "") for m in modelos_crudos if "gemini" in m.name.lower() and not any(p in m.name.lower() for p in palabras_prohibidas)]
            lista_final.sort(reverse=True)
            return lista_final
        except Exception as e:
            print(f"[Modelo Error]: {e}")
            return [
                "gemini-flash-lite-latest",
                "gemini-flash-latest",
                "gemini-3-flash-preview",
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash"
            ]

    def abrir_selector_modelo(self):
        toplevel = ctk.CTkToplevel(self)
        toplevel.title("Seleccionar Modelo IA")
        w, h = 300, 420
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        toplevel.geometry(f"{w}x{h}+{x}+{y}")
        toplevel.attributes("-topmost", True)
        ctk.CTkLabel(toplevel, text="Modelos Disponibles", font=("Arial", 14, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(toplevel, width=250, height=250)
        scroll.pack(pady=10, padx=10)
        
        # Acceso global para MODELO_ACTUAL
        import config
        var_modelo = ctk.StringVar(value=config.MODELO_ACTUAL)
        for m in self.obtener_modelos_disponibles():
            ctk.CTkRadioButton(scroll, text=m, variable=var_modelo, value=m).pack(anchor="w", pady=5, padx=5)

        def guardar_modelo():
            nuevo = var_modelo.get()
            config.MODELO_ACTUAL = nuevo
            try:
                env_path = self.ruta_base / ".env"
                lines = open(env_path).readlines() if env_path.exists() else []
                with open(env_path, "w") as f:
                    found = False
                    for l in lines:
                        if l.startswith("GENAI_MODEL="): f.write(f"GENAI_MODEL={nuevo}\n"); found = True
                        else: f.write(l)
                    if not found: f.write(f"GENAI_MODEL={nuevo}\n")
                os.environ["GENAI_MODEL"] = nuevo
                self.lbl_modelo_actual_ui.configure(text=f"Modelo: {nuevo}")
                toplevel.destroy()
                messagebox.showinfo("Modelo Actualizado", f"Se usará: {nuevo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

        ctk.CTkButton(toplevel, text="GUARDAR CAMBIOS", command=guardar_modelo).pack(pady=10)
        ctk.CTkLabel(toplevel, text="Algunos modelos podrían ser de pago", font=("Arial", 10), text_color="gray").pack(pady=(0, 10))

    def seleccionar_archivo(self):
        archivo = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if archivo:
            self.ruta_archivo_pdf = archivo
            self.lbl_archivo.configure(text=f"Archivo: {os.path.basename(archivo)}")
            if self.api_ready:
                self.btn_ejecutar.configure(state="normal")
                self.option_autor.configure(state="normal")
            self._escribir_seguro(self.textbox, f"\n[System]: Cargado {os.path.basename(archivo)}\n")

    def activar_progreso(self, activo):
        if activo: self.progressbar.grid(); self.progressbar.start()
        else: self.progressbar.stop(); self.progressbar.grid_remove()

    def ejecutar_agente(self):
        self.btn_ejecutar.configure(state="disabled")
        self.option_autor.configure(state="disabled") 
        self.activar_progreso(True)
        print(f"[Terminal]: Iniciando análisis con {self.option_autor.get()}...")
        threading.Thread(target=self._proceso_ia, args=(self.option_autor.get(), self.entry_perspectiva.get()), daemon=True).start()

    def _proceso_ia(self, autor_nombre, perspectiva_usuario):
        try:
            print("[Terminal]: Enviando prompt a Google Gemini...")
            reader = PdfReader(self.ruta_archivo_pdf)
            texto_relato = "\n".join([p.extract_text() for p in reader.pages])
            texto_relato = "\n".join([p.extract_text() for p in reader.pages])
            
            # Obtención del perfil desde el nuevo estructura JSON (Diccionario o String)
            datos_autor = DICCIONARIO_AUTORES.get(autor_nombre, {})
            
            if isinstance(datos_autor, dict):
                descripcion = datos_autor.get("descripcion", "Eres un asistente literario experto.")
                ejemplos = datos_autor.get("ejemplos_few_shot", [])
                
                # Construcción del System Instruction enriquecido
                perfil_autor = descripcion
                if ejemplos:
                    perfil_autor += "\n\nEJEMPLOS DE ESTILO (FEW-SHOT):\n" + "\n".join([f"- {ex}" for ex in ejemplos])
            else:
                # Fallback por si acaso sigue siendo string (ej. versiones antiguas o error de carga)
                perfil_autor = str(datos_autor)

            self.autor_actual = autor_nombre
            self.perfil_autor_actual = perfil_autor

            prompt = (
                "IMPORTANTE: RESPONDE ÚNICAMENTE CON UN JSON VÁLIDO. NO ESCRIBAS NADA FUERA DEL JSON.\n"
                "El JSON debe tener exactamente estas 4 claves:\n"
                "- 'titulos': [Lista de 3 títulos sugeridos]\n"
                "- 'sinopsis': 'Texto de la sinopsis'\n"
                "- 'conceptos': [Lista de 5 conceptos clave]\n"
                "- 'analisis_autor': 'Texto del análisis profundo según tu estilo personal'\n\n"
            )
            if perspectiva_usuario: prompt += f"NOTA DE CONTEXTO ADICIONAL: {perspectiva_usuario}\n"
            prompt_final = f"TEXTO A ANALIZAR:\n{texto_relato}\n\n{prompt}"

            config_gen = types.GenerateContentConfig(system_instruction=perfil_autor, response_mime_type="application/json")
            
            # Refenciando config.MODELO_ACTUAL
            import config
            response = self.client.models.generate_content(model=config.MODELO_ACTUAL, contents=prompt_final, config=config_gen)
            print("[Terminal]: Respuesta recibida. Procesando JSON...")
            datos_json = json.loads(response.text)
            self.after(0, self._finalizar_ia, datos_json, autor_nombre)
        except Exception as e:
            err = str(e)
            if any(x in err for x in ["429", "ResourceExhausted", "Quota"]):
                self.after(0, self._preguntar_cambio_modelo, err)
            else:
                self.after(0, self._error_ia, err)

    def _preguntar_cambio_modelo(self, error_msg):
        self.activar_progreso(False)
        import config
        if messagebox.askyesno("Error de Modelo", f"Error de cuota con '{config.MODELO_ACTUAL}'.\n¿Desea cambiar de modelo?"):
            self.abrir_selector_modelo()
        else: self._error_ia(f"Cancelado por cuota: {error_msg}")

    def _finalizar_ia(self, datos_json, autor_nombre):
        self.activar_progreso(False)
        texto = f"=== ANÁLISIS DE CRÍTICO: {autor_nombre.upper()} ===\n\n"
        if 'analisis_autor' in datos_json: texto += f"LA MIRADA CRÍTICA:\n{datos_json['analisis_autor']}\n\n"
        if self.sinopsis_var.get() and 'sinopsis' in datos_json: texto += f"SINOPSIS NARRATIVA:\n{datos_json['sinopsis']}\n\n"
        if self.titulos_var.get() and 'titulos' in datos_json: texto += "TÍTULOS ALTERNATIVOS:\n" + "\n".join([f"- {t}" for t in datos_json['titulos']]) + "\n\n"
        if self.conceptos_var.get() and 'conceptos' in datos_json: texto += f"CONCEPTOS CLAVE:\n{', '.join(datos_json['conceptos'])}\n"

        self._escribir_seguro(self.textbox, texto, modo="overwrite") 
        self.datos_json_actual = datos_json 
        self.reporte_actual_guardado = False 
        self.btn_conversar.grid()
        self.btn_conversar.configure(state="normal")
        self.historial_coloquio = []
        self.chat_session = None
        
        self._guardar_automatico(datos_json, autor_nombre)
        self._validar_email_input()

    def _error_ia(self, error):
        self.activar_progreso(False)
        self._escribir_seguro(self.textbox, f"\n[ERROR]: {error}\n")
        self.btn_ejecutar.configure(state="normal")

    def abrir_coloquio(self):
        if self.ventana_coloquio and self.ventana_coloquio.winfo_exists():
            self.ventana_coloquio.lift(); return

        if not self.chat_session and self.api_ready:
            import config
            try:
                self.chat_session = self.client.chats.create(
                    model=config.MODELO_ACTUAL,
                    config=types.GenerateContentConfig(system_instruction=self.perfil_autor_actual, temperature=0.7)
                )
            except Exception as e:
                self._escribir_seguro(self.textbox, f"\n[ERROR CHAT]: {e}\n"); return

        self.ventana_coloquio = ctk.CTkToplevel(self)
        self.ventana_coloquio.title(f"Coloquio con {self.autor_actual}")
        w, h = 600, 550
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        self.ventana_coloquio.geometry(f"{w}x{h}+{x}+{y}")
        self.ventana_coloquio.attributes("-topmost", True)
        self.ventana_coloquio.protocol("WM_DELETE_WINDOW", self.cerrar_coloquio)

        frame = ctk.CTkFrame(self.ventana_coloquio)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display = ctk.CTkTextbox(frame, state="disabled", font=("Consolas", 11), wrap="word")
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.progress_chat = ctk.CTkProgressBar(frame, height=5)
        self.progress_chat.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_chat.pack_forget()

        self._escribir_seguro(self.chat_display, f"--- Iniciando conversación con {self.autor_actual} ---\n\n", modo="insert_start")
        for a, m in self.historial_coloquio:
            n = self.autor_actual if a == "Autor" else "Usted"
            self._escribir_seguro(self.chat_display, f"{n}: {m}\n\n")

        inp_frame = ctk.CTkFrame(self.ventana_coloquio, height=50)
        inp_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.chat_entry = ctk.CTkEntry(inp_frame, placeholder_text="Escriba su mensaje...")
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.chat_entry.bind("<Return>", self._enviar_mensaje_coloquio)
        ctk.CTkButton(inp_frame, text="ENVIAR", width=80, command=self._enviar_mensaje_coloquio).pack(side="right", padx=5)

        # Botón de Cierre
        btn_cerrar = ctk.CTkButton(self.ventana_coloquio, text="CERRAR CONVERSACIÓN",
                                   fg_color="#444", hover_color="#333",
                                   command=self.cerrar_coloquio)
        btn_cerrar.pack(pady=(0, 10))

    def _enviar_mensaje_coloquio(self, event=None):
        msg = self.chat_entry.get().strip()
        if not msg: return
        self.chat_entry.delete(0, "end")
        self._append_chat_display("Usted", msg)
        self.historial_coloquio.append(("Usuario", msg))
        self.progress_chat.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_chat.start()
        threading.Thread(target=self._procesar_respuesta_chat, args=(msg,), daemon=True).start()

    def _procesar_respuesta_chat(self, msg_user):
        try:
            resp = self.chat_session.send_message(msg_user)
            txt = resp.text if resp and resp.text else "[El autor permanece en silencio...]"
            self.after(0, self._append_chat_display, self.autor_actual, txt)
            self.historial_coloquio.append(("Autor", txt))
        except Exception as e:
            err = str(e)
            m = "El autor está reflexionando profundamente..." if any(x in err for x in ["429", "Quota"]) else f"Error: {e}"
            self.after(0, self._append_chat_display, "SISTEMA", m)
        finally:
            self.progress_chat.stop(); self.after(0, self.progress_chat.pack_forget)

    def _append_chat_display(self, remitente, texto):
        self.reporte_actual_guardado = False
        if self.ventana_coloquio and self.ventana_coloquio.winfo_exists():
            self._escribir_seguro(self.chat_display, f"{remitente}: {texto}\n\n")

    def cerrar_coloquio(self):
        if self.ventana_coloquio:
            self.ventana_coloquio.destroy(); self.ventana_coloquio = None
        self.btn_conversar.configure(state="disabled"); self.btn_conversar.grid_remove() 
        if self.historial_coloquio:
             self._guardar_automatico(self.datos_json_actual, self.autor_actual)
             self._escribir_seguro(self.textbox, "\n[System]: Reporte actualizado con coloquio.\n")

    def _validar_email_input(self, event=None):
        self.btn_enviar.configure(state="normal" if self.entry_emails.get().strip() and self.datos_json_actual else "disabled")

    def _guardar_automatico(self, datos_json, autor_nombre):
        try:
            import config
            folder = config.DIRECTORIO_INFORMES
            folder.mkdir(parents=True, exist_ok=True)
            name = f"Analisis_{limpiar_texto(os.path.basename(self.ruta_archivo_pdf).split('.')[0])}_{limpiar_texto(autor_nombre)}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
            path = folder / name
            print(f"[Terminal]: Generando DOCX en {path}...")
            GestorWord.crear_documento(str(path), datos_json, autor_nombre, self.historial_coloquio)
            self.ruta_ultimo_word = str(path)
            self.reporte_actual_guardado = True
            self._escribir_seguro(self.textbox, f"\n[System]: Reporte guardado: {name}\n")
            self._validar_email_input()
            return str(path)
        except Exception as e:
            self._escribir_seguro(self.textbox, f"\n[ERROR AUTOSAVE]: {e}\n"); return ""

    def enviar_reporte_email(self):
        dest = self.entry_emails.get()
        if not dest or not self.ruta_ultimo_word or not os.path.exists(self.ruta_ultimo_word): return
        print(f"[Terminal]: Preparando envío a {dest}...")
        self.cerrar_coloquio()
        self.btn_enviar.configure(state="disabled"); self.activar_progreso(True)
        threading.Thread(target=self._proceso_email, args=(dest,), daemon=True).start()

    def _proceso_email(self, destinatarios):
        try:
            lista = [m.strip() for m in destinatarios.split(',')]
            servidor = smtplib.SMTP('smtp.mail.yahoo.com', 587)
            servidor.starttls(); servidor.login(str(MAIL_USER), str(MAIL_PASS))
            for mail in lista:
                msg = MIMEMultipart()
                msg['From'], msg['To'], msg['Subject'] = str(MAIL_USER), mail, f"Análisis: {os.path.basename(self.ruta_archivo_pdf)}"
                msg.attach(MIMEText("Adjunto encontrará el análisis solicitado.\n\nAtte,\nEl Bufón.", 'plain'))
                for fpath in [self.ruta_ultimo_word, self.ruta_archivo_pdf]:
                    if fpath and os.path.exists(fpath):
                        with open(fpath, "rb") as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(fpath))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(fpath)}"'
                            msg.attach(part)
                servidor.send_message(msg)
            servidor.quit()
            self.after(0, lambda: self._finalizar_email(True))
        except Exception as e:
            self.after(0, lambda: self._finalizar_email(False, str(e)))

    def _finalizar_email(self, exito, error=""):
        self.activar_progreso(False); self.btn_enviar.configure(state="normal")
        m = "\n[System]: Correos enviados exitosamente.\n" if exito else f"\n[ERROR EMAIL]: {error}\n"
        self._escribir_seguro(self.textbox, m)

    def limpiar_interfaz(self):
        self.ruta_archivo_pdf = ""; self.ruta_ultimo_word = ""
        self.lbl_archivo.configure(text="Archivo: Ninguno")
        self._escribir_seguro(self.textbox, "--- Sistema Restablecido ---\n", modo="overwrite")
        self.option_autor.configure(state="normal"); self.btn_ejecutar.configure(state="disabled")
        self.btn_enviar.configure(state="disabled"); self.btn_conversar.grid_remove()
        if self.ventana_coloquio: self.ventana_coloquio.destroy()
        self.ventana_coloquio = None; self.historial_coloquio = []; self.chat_session = None
        self.datos_json_actual = {}; self.reporte_actual_guardado = False
