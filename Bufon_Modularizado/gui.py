import sys
import os
import customtkinter as ctk
import threading
import json
from PyPDF2 import PdfReader
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

# Importaciones de módulos locales
from config import API_KEY, MODELO_ACTUAL, DICCIONARIO_AUTORES, DIRECTORIO_INFORMES, USANDO_FALLBACK, ESTADO_DIRECTORIO, ESTADO_CARGA_AUTORES
from utils import ToolTip, limpiar_texto, estimar_peso_texto
from gestor_word import GestorWord
from agente_ia import AgenteIA
from gestor_email import GestorEmail
from ventanas import VentanaAjustes, VentanaSelectorModelo, VentanaColoquio

# ==============================================================================
# INTERFAZ GRÁFICA - v0.9.8m
# ==============================================================================

class ElBufonSemiotico(ctk.CTk):
    """
    Clase principal de la interfaz. Versión v0.9.8m (Arquitectura Modular).
    """
    def __init__(self):
        super().__init__()

        # --- CONFIGURACIÓN BÁSICA DE LA VENTANA ---
        self.title("EL BUFÓN SEMIÓTICO v0.9.8m (Arquitectura Modular)")
        self.geometry("1100x650")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- BARRA DE ESTADO (Inicialización Temprana) ---
        # Se inicializa al principio para interceptar logs de arranque sin crash.
        self.status_bar_frame = ctk.CTkFrame(self, height=25, corner_radius=0, fg_color="transparent")
        self.status_bar_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        
        self.lbl_status = ctk.CTkLabel(self.status_bar_frame, text="Iniciando sistema...", anchor="w", font=("Consolas", 11), text_color="gray")
        self.lbl_status.pack(side="left", padx=10, fill="x", expand=True)
        
        self.status_tooltip = ToolTip(self.lbl_status, "Estado del sistema")
        

        # Variables de estado
        self.ruta_archivo_pdf = ""
        self.ruta_ultimo_word = ""

        # Instancias de lógica de negocio
        self.agente_ia = AgenteIA()
        self.gestor_email = GestorEmail()
        
        self.api_ready = self.agente_ia.api_ready

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
        
        # [v0.9.7.7m] Nombre de archivo de sesión persistente (Una Sesión = Un Archivo)
        self.nombre_archivo_sesion = None

        # --- BARRA LATERAL (SIDEBAR) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # Logo y Versión
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="EL BUFÓN\nSEMIÓTICO", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 0))
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text="v0.9.8m", font=ctk.CTkFont(size=10), text_color="gray")
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Botón Cargar
        self.btn_cargar = ctk.CTkButton(self.sidebar_frame, text="CARGAR RELATO", command=self.seleccionar_archivo)
        self.btn_cargar.grid(row=2, column=0, padx=20, pady=10)

        # Selector Crítico
        self.lbl_critico = ctk.CTkLabel(self.sidebar_frame, text="CRÍTICO INVITADO:", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_critico.grid(row=3, column=0, padx=20, pady=(15, 5))

        # [v0.9.7.7m] Selector Origen (Nacional / Internacional)
        self.filtro_origen = ctk.StringVar(value="Nacional")
        self.seg_origen = ctk.CTkSegmentedButton(self.sidebar_frame, values=["Nacional", "Internacional"],
                                                 variable=self.filtro_origen,
                                                 command=self._filtrar_autores)
        self.seg_origen.grid(row=4, column=0, padx=20, pady=(0, 5)) 

        # [v0.9.7.7m] Inicialización dinámica, se poblará con _filtrar_autores
        self.option_autor = ctk.CTkOptionMenu(self.sidebar_frame, values=[]) 
        self.option_autor.grid(row=5, column=0, padx=20, pady=(0, 10))

        # Opciones
        self.lbl_opciones = ctk.CTkLabel(self.sidebar_frame, text="OPCIONES DE ANÁLISIS:", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_opciones.grid(row=6, column=0, padx=20, pady=(15, 5))

        self.titulos_var = ctk.BooleanVar(value=True)
        self.sinopsis_var = ctk.BooleanVar(value=True)
        self.conceptos_var = ctk.BooleanVar(value=True)

        chk_font = ctk.CTkFont(size=12)
        self.chk_1 = ctk.CTkCheckBox(self.sidebar_frame, text="Títulos Alternativos", variable=self.titulos_var, 
                                     font=chk_font, checkbox_width=18, checkbox_height=18, corner_radius=4)
        self.chk_1.grid(row=7, column=0, padx=20, pady=(5, 0), sticky="w")
        self.chk_2 = ctk.CTkCheckBox(self.sidebar_frame, text="Sinopsis", variable=self.sinopsis_var,
                                     font=chk_font, checkbox_width=18, checkbox_height=18, corner_radius=4)
        self.chk_2.grid(row=8, column=0, padx=20, pady=(5, 0), sticky="w")
        self.chk_3 = ctk.CTkCheckBox(self.sidebar_frame, text="Conceptos Clave", variable=self.conceptos_var,
                                     font=chk_font, checkbox_width=18, checkbox_height=18, corner_radius=4)
        self.chk_3.grid(row=9, column=0, padx=20, pady=(5, 0), sticky="w")

        # Apariencia
        self.lbl_apariencia = ctk.CTkLabel(self.sidebar_frame, text="Apariencia:", anchor="w")
        self.lbl_apariencia.grid(row=11, column=0, padx=20, pady=(10, 0))
        self.option_apariencia = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                   command=self.cambiar_apariencia)
        self.option_apariencia.grid(row=12, column=0, padx=20, pady=(10, 10))

        # Status y Ajustes
        self.status_indicator = ctk.CTkLabel(self.sidebar_frame, text="...", font=ctk.CTkFont(size=10, weight="bold"))
        self.status_indicator.grid(row=13, column=0, padx=20, pady=(5, 0))

        # Indicador de Conectividad Real
        self.lbl_conexion = ctk.CTkLabel(self.sidebar_frame, text="○ PROBANDO RED...", 
                                         font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFA000")
        self.lbl_conexion.grid(row=14, column=0, padx=20, pady=(0, 0))

        # Indicador de Modelo
        self.lbl_modelo_actual_ui = ctk.CTkLabel(self.sidebar_frame, text=f"Modelo: {MODELO_ACTUAL}", 
                                                 font=ctk.CTkFont(size=10), text_color="gray")
        self.lbl_modelo_actual_ui.grid(row=15, column=0, padx=20, pady=(0, 5))



        self.btn_ajustes = ctk.CTkButton(self.sidebar_frame, text="⚙️ Ajustes", 
                                         fg_color="transparent", border_width=1, 
                                         text_color=("gray10", "#DCE4EE"), border_color=("gray10", "#DCE4EE"),
                                         command=self.abrir_ajustes)
        self.btn_ajustes.grid(row=16, column=0, padx=20, pady=(5, 10))
        ToolTip(self.btn_ajustes, "Accede a las opciones de configuración del agente, email del remitente y api keys indispensables")



        # [v0.9.7.7m] Inicializar filtro por defecto
        self._filtrar_autores("Nacional")

        # --- ÁREA PRINCIPAL ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        # [v0.9.8m] Barra de Enfoque Rápido ("Chips")
        # Ajuste: Diseño refinado tipo "Chips" y botón de limpieza
        self.frame_chips = ctk.CTkFrame(self.header_frame, fg_color="transparent", height=30)
        self.frame_chips.pack(pady=(0, 5))

        focos = [
            ("🏰 Trama", "Analiza la estructura y el ritmo.", "Estructura y Causalidad"),
            ("✍️ Estilo", "Examina la sintaxis y la voz narrativa.", "Sintaxis y Voz"),
            ("🎭 Personajes", "Profundiza en la psicología de los personajes.", "Psicología"),
            ("🔥 Final", "Evalúa la efectividad del cierre.", "Cierre y Clímax"),
            ("🩸 Despiadado", "Sé brutalmente honesto con los errores.", "Crítica Dura")
        ]

        for texto_btn, texto_inyectar, tooltip_msg in focos:
            # Estilos por defecto (Chips Minimalistas)
            fg_color = "transparent"
            border_color = "#666"
            text_color = "gray90"
            hover_color = "#444"
            width_btn = 90 # Un poco más anchos que altos para parecer chips

            # Estilo Especial para "Despiadado"
            if "Despiadado" in texto_btn:
                fg_color = "#2A0A0A"      # Rojo muy oscuro fondo
                border_color = "#8B0000"  # Rojo sangre borde
                text_color = "#FF9999"    # Texto rojizo
                hover_color = "#440000"   # Hover rojo oscuro

            btn = ctk.CTkButton(self.frame_chips, text=texto_btn, 
                                command=lambda t=texto_inyectar: self._inyectar_foco(t),
                                height=24, width=width_btn, corner_radius=12,
                                font=ctk.CTkFont(size=11),
                                fg_color=fg_color, 
                                border_width=1, border_color=border_color,
                                text_color=text_color, hover_color=hover_color)
            btn.pack(side="left", padx=3)
            ToolTip(btn, tooltip_msg)
        
        # Botón de Limpieza (🧹)
        self.btn_limpiar_foco = ctk.CTkButton(self.frame_chips, text="🧹", 
                                              command=self._limpiar_foco,
                                              height=24, width=30, corner_radius=12,
                                              font=ctk.CTkFont(size=12),
                                              fg_color="#333", hover_color="#000")
        self.btn_limpiar_foco.pack(side="left", padx=(10, 0))
        ToolTip(self.btn_limpiar_foco, "Limpiar instrucciones adicionales")

        self.entry_perspectiva = ctk.CTkEntry(self.header_frame, placeholder_text="Seleccione un enfoque arriba o escriba una instrucción...", height=35)
        self.entry_perspectiva.pack(fill="x", pady=(0, 10))
        # Ajuste: Campo vacío al inicio
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
            self.textbox._textbox.tag_config("warning_msg", foreground="#FF5555", font=("Courier New", 10, "bold"))
        except Exception:
            pass
        
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
        self.btn_conversar.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.btn_conversar.grid_remove() # Oculto al inicio

        # --- BARRA DE ESTADO (Movida al inicio) ---
        # El código anterior se ha eliminado de aquí.

        # Inicialización del cliente genai (Ahora manejado por AgenteIA al instanciar)
        self.verificar_estado_sistema()

        # [v0.9.7.6m] Verificar estado de carga de autores al final del arranque
        if ESTADO_CARGA_AUTORES == "FALTANTE":
            self._escribir_seguro(self.textbox, "[ALERTA]: No se encontró 'perfiles_autores.json'. Funcionalidad de críticos limitada.", destino="status")
            self._deshabilitar_controles_criticos()
        elif ESTADO_CARGA_AUTORES == "ERROR_SINTAXIS":
            self._escribir_seguro(self.textbox, "[ERROR]: 'perfiles_autores.json' corrupto. Revise el formato JSON.", destino="status")
            self._deshabilitar_controles_criticos()

    def _deshabilitar_controles_criticos(self):
        """Deshabilita controles que dependen de los autores."""
        self.btn_ejecutar.configure(state="disabled")
        self.option_autor.set(" ¡¡Sin AUTORES!!")
        self.option_autor.configure(state="disabled")
        self.api_ready = False # Previene reactivación al cargar PDF

    def _escribir_seguro(self, widget, texto, modo="append", destino="chat"):
        """
        Escribe en el widget de forma segura (thread-safe).
        Si destino="chat" (default), verifica si es mensaje de sistema para redirigir a status bar.
        """
        try:
            # Lógica de redirección a Status Bar
            # Interceptamos: [ALERTA], [WARNING], [System], [AVISO], [ALERTA RUTA], [AVISO SISTEMA], [FALLBACK]
            es_log_sistema = texto.lstrip().startswith(("[System]", "[Terminal]", "[ALERTA]", "[WARNING]", "[AVISO]", "[FALLBACK]", "[ALERTA RUTA]", "[AVISO SISTEMA]"))
            
            if destino == "status" or (destino == "chat" and es_log_sistema):
                # Limpiar texto de saltos de línea excesivos
                texto_limpio = texto.strip()
                if not texto_limpio: return # Ignorar líneas vacías en status bar

                # Formatear para barra de estado (una línea) y tooltip (multilínea)
                texto_barra = texto_limpio.replace("\n", " | ")
                self.lbl_status.configure(text=texto_barra)
                
                # Actualizar el tooltip con el mensaje completo
                self.status_tooltip.text = texto_limpio
                
                # Color según severidad
                # Si contiene ALERTA, WARNING, AVISO, FALLBACK -> Rojo/Naranja
                # Si es System, Terminal -> Gris
                upper_text = texto.upper()
                if any(tag in upper_text for tag in ["ALERTA", "WARNING", "AVISO", "FALLBACK"]):
                    self.lbl_status.configure(text_color="#FF5555") # Rojo claro para alertas
                else:
                    self.lbl_status.configure(text_color="gray") # Gris para info normal
                return

            # Si no es log de sistema, escribir en el Chat (Textbox)
            widget.configure(state="normal")
            
            tags_to_apply = ()
            # Mantener lógica de tags por si acaso se fuerza escritura en chat con destino="chat" explicito y sin tags de sistema
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
                     widget._textbox.tag_add(tags_to_apply[0], start_index, f"{start_index}+{count}c")
                except:
                     pass

            widget.see("end" if modo == "append" else "0.0")
            widget.configure(state="disabled")
        except Exception as e:
            print(f"[UI Error]: Falló escritura segura -> {e}")



    def _test_conexion_thread(self):
        conectado = self.agente_ia.verificar_conexion()
        # Actualizar UI desde el hilo principal
        self.after(0, lambda: self._actualizar_lbl_conexion(conectado))

    def _actualizar_lbl_conexion(self, conectado):
        if conectado:
            self.lbl_conexion.configure(text="● API CONECTADA", text_color="#4CAF50") # Verde
        else:
            self.lbl_conexion.configure(text="● SIN CONEXIÓN", text_color="#FF5555") # Rojo

    def verificar_estado_sistema(self):
        """
        [Refactorizado v0.9.7.7m] Validación Jerárquica:
        - Nivel 1 (Crítico): API Key. Habilita análisis y check de conexión.
        - Nivel 2 (Opcional): Email. Habilita envío de reportes.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")
        
        # Nivel 1: API Key (Crítico)
        if api_key:
            self.status_indicator.configure(text="● SISTEMA LISTO", text_color="#4CAF50")
            self.api_ready = True
            
            # Habilitar análisis si hay archivo cargado
            if self.ruta_archivo_pdf:
                self.btn_ejecutar.configure(state="normal")
                # El selector de autores también debe habilitarse si hay API y archivo
                self.option_autor.configure(state="normal")
            
            # Iniciar prueba de conexión SIEMPRE que haya API Key (Independiente del mail)
            threading.Thread(target=self._test_conexion_thread, daemon=True).start()

            # Limpiar alertas previas de bloqueo crítico
            contenido_actual = self.textbox.get("1.0", "end")
            if "[ALERTA]: Faltan configuraciones" in contenido_actual:
                 self._escribir_seguro(self.textbox, "--- El sistema espera su consulta ---\n", modo="overwrite")
        else:
            # Caso Crítico: Falta API Key - BLOQUEO TOTAL
            self.status_indicator.configure(text="○ CONFIGURACIÓN PENDIENTE", text_color="#FFA000")
            self.lbl_conexion.configure(text="○ NO CONECTADO", text_color="gray")
            self.btn_ejecutar.configure(state="disabled")
            self.option_autor.configure(state="disabled")
            self.api_ready = False
            self._escribir_seguro(self.textbox, "\n[ALERTA]: Falta API KEY. Configure en '⚙️ Ajustes'.\n")
            
            # Si falta lo principal, desactivamos lo secundario también por seguridad
            self.btn_enviar.configure(state="disabled")
            self.entry_emails.configure(state="disabled")
            return # Salir, no tiene sentido validar email sin core
            
        # Nivel 2: Email (Opcional)
        if email_user and email_pass:
            # Habilitar funcionalidad de correo
            self.entry_emails.configure(state="normal", placeholder_text="Correos colaboradores (separados por coma)...")
            # El botón de enviar se gestiona dinámicamente según contenido de entry y reporte existente, 
            # pero aseguramos que entry esté operativo.
        else:
            # Deshabilitar funcionalidad de correo (pero NO bloquear sistema)
            self.btn_enviar.configure(state="disabled")
            self.entry_emails.configure(state="disabled", placeholder_text="Email no configurado (Opcional)")
            self._escribir_seguro(self.textbox, "[AVISO]: Credenciales de correo no configuradas. Función de envío desactivada.", destino="status")

    def _limpiar_foco(self):
        """Limpia el contenido del entry de perspectiva."""
        self.entry_perspectiva.delete(0, "end")
        self.entry_perspectiva.focus()

    def _inyectar_foco(self, texto_nuevo):
        """Inyecta texto de enfoque en el entry de perspectiva."""
        texto_actual = self.entry_perspectiva.get().strip()
        self.entry_perspectiva.delete(0, "end")
        
        if texto_actual:
            if texto_nuevo not in texto_actual: # Evitar duplicados exactos simples
                nuevo_contenido = f"{texto_actual}, {texto_nuevo}"
            else:
                nuevo_contenido = texto_actual
        else:
            nuevo_contenido = texto_nuevo
            
        self.entry_perspectiva.insert(0, nuevo_contenido)
        self.entry_perspectiva.focus() # Dar foco visual

    def abrir_ajustes(self):
        VentanaAjustes(self)

    def cambiar_apariencia(self, nuevo_modo):
        ctk.set_appearance_mode(nuevo_modo)

    def obtener_modelos_disponibles(self):
        return self.agente_ia.obtener_modelos_disponibles()

    def abrir_selector_modelo(self):
        VentanaSelectorModelo(self)

    def seleccionar_archivo(self):
        archivo = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if archivo:
            self.ruta_archivo_pdf = archivo
            
            # Estimación de Tokens
            try:
                reader = PdfReader(archivo)
                texto_raw = ""
                for page in reader.pages:
                    texto_raw += page.extract_text() or ""
                
                tokens, etiqueta, color = estimar_peso_texto(texto_raw)
                
                self.lbl_archivo.configure(
                    text=f"Archivo: {os.path.basename(archivo)} | ~{tokens} tokens ({etiqueta})",
                    text_color=color
                )
            except Exception as e:
                print(f"[ERROR LECTURA PDF]: {e}")
                self.lbl_archivo.configure(text=f"Archivo: {os.path.basename(archivo)} | (Error al leer tokens)", text_color="gray")

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
        
        # [v0.9.7.7m] Congelar nombre de archivo para toda la sesión
        # Al inicio del análisis se define el nombre único que tendrá el archivo
        try:
            autor_safe = limpiar_texto(self.option_autor.get())
            pdf_name_safe = limpiar_texto(os.path.basename(self.ruta_archivo_pdf).split('.')[0])
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            self.nombre_archivo_sesion = f"Analisis_{pdf_name_safe}_{autor_safe}_{timestamp}.docx"
            print(f"[Terminal]: Sesión iniciada. Archivo destino congelado: {self.nombre_archivo_sesion}")
        except Exception as e:
            print(f"[ERROR]: Fallo al generar nombre sesión: {e}")
            self.nombre_archivo_sesion = None

        print(f"[Terminal]: Iniciando análisis con {self.option_autor.get()}...")
        threading.Thread(target=self._proceso_ia, args=(self.option_autor.get(), self.entry_perspectiva.get()), daemon=True).start()

    def _proceso_ia(self, autor_nombre, perspectiva_usuario):
        try:
            print("[Terminal]: Enviando prompt a Google Gemini...")
            reader = PdfReader(self.ruta_archivo_pdf)
            texto_relato = "\n".join([p.extract_text() for p in reader.pages])
            
            self.autor_actual = autor_nombre
            # self.perfil_autor_actual ya no se usa aquí, lo maneja el agente internamente

            # Llamada al AgenteIA (Bloqueante)
            datos_json = self.agente_ia.procesar_analisis(texto_relato, autor_nombre, perspectiva_usuario)
            
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
            VentanaSelectorModelo(self)
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
        
        self.historial_coloquio = []
        self.chat_session = None
        
        self._guardar_automatico(datos_json, autor_nombre)
        self._validar_email_input()

    def _filtrar_autores(self, origen_seleccionado):
        """
        [v0.9.7.7m] Filtra la lista de autores según su origen y actualiza el OptionMenu.
        """
        autores_filtrados = []
        for nombre, datos in DICCIONARIO_AUTORES.items():
            # Si no tiene clave 'origen', asumimos 'Nacional' por compatibilidad
            origen_autor = datos.get("origen", "Nacional")
            
            if origen_autor == origen_seleccionado:
                autores_filtrados.append(nombre)
        
        # Ordenar alfabéticamente
        autores_filtrados.sort()

        # Actualizar valores del OptionMenu
        if autores_filtrados:
            self.option_autor.configure(values=autores_filtrados)
            self.option_autor.set(autores_filtrados[0])
            self.option_autor.configure(state="normal")
        else:
            self.option_autor.configure(values=["Sin autores"])
            self.option_autor.set("Sin autores")
            self.option_autor.configure(state="disabled")

    def _error_ia(self, error):
        self.activar_progreso(False)
        self._escribir_seguro(self.textbox, f"\n[ERROR]: {error}\n")
        self.btn_ejecutar.configure(state="normal")

    def abrir_coloquio(self):
        if self.ventana_coloquio and self.ventana_coloquio.winfo_exists():
            self.ventana_coloquio.lift(); return
        
        # Si no hay sesión, se inicia en VentanaColoquio o aquí antes. 
        # VentanaColoquio maneja el inicio si detecta None.
        self.ventana_coloquio = VentanaColoquio(self, self.autor_actual)

    # Métodos eliminados y delegados a ventanas.py:
    # - abrir_ajustes -> VentanaAjustes
    # - abrir_selector_modelo -> VentanaSelectorModelo
    # - manejo de chat -> VentanaColoquio

    def _validar_email_input(self, event=None):
        self.btn_enviar.configure(state="normal" if self.entry_emails.get().strip() and self.datos_json_actual else "disabled")

    def _guardar_automatico(self, datos_json, autor_nombre):
        try:
            import config
            folder = config.DIRECTORIO_INFORMES
            folder.mkdir(parents=True, exist_ok=True)
            
            # [v0.9.7.7m] Usar nombre de sesión congelado si existe
            if self.nombre_archivo_sesion:
                name = self.nombre_archivo_sesion
            else:
                # Fallback defensivo
                name = f"Analisis_{limpiar_texto(os.path.basename(self.ruta_archivo_pdf).split('.')[0])}_{limpiar_texto(autor_nombre)}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"

            path = folder / name
            print(f"[Terminal]: Generando/Actualizando DOCX en {path}...")
            GestorWord.crear_documento(str(path), datos_json, autor_nombre, self.historial_coloquio)
            self.ruta_ultimo_word = str(path)
            self.reporte_actual_guardado = True
            self._escribir_seguro(self.textbox, f"\n[System]: Reporte actualizado: {name}\n")
            self._validar_email_input()
            return str(path)
        except Exception as e:
            self._escribir_seguro(self.textbox, f"\n[ERROR AUTOSAVE]: {e}\n"); return ""

    def enviar_reporte_email(self):
        dest = self.entry_emails.get()
        if not dest or not self.ruta_ultimo_word or not os.path.exists(self.ruta_ultimo_word): return
        print(f"[Terminal]: Preparando envío a {dest}...")
        if self.ventana_coloquio and self.ventana_coloquio.winfo_exists():
             self.ventana_coloquio.cerrar()
        self.btn_enviar.configure(state="disabled"); self.activar_progreso(True)
        threading.Thread(target=self._proceso_email, args=(dest,), daemon=True).start()

    def _proceso_email(self, destinatarios):
        try:
            self.gestor_email.enviar_reporte(destinatarios, self.ruta_ultimo_word, self.ruta_archivo_pdf)
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
        self.nombre_archivo_sesion = None # [v0.9.7.7m] Resetear sesión
