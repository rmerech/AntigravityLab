import customtkinter as ctk
import os
import threading
from tkinter import messagebox, filedialog
from pathlib import Path
from utils import ToolTip

# ==============================================================================
# MÓDULO DE VENTANAS SECUNDARIAS - v0.9.8m
# ==============================================================================

class VentanaAjustes(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Ajustes del Sistema")
        ancho = 420
        alto = 550
        x = self.master_app.winfo_x() + (self.master_app.winfo_width() // 2) - (ancho // 2)
        y = self.master_app.winfo_y() + (self.master_app.winfo_height() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.attributes("-topmost", True)
        
        self.crear_interfaz()

    def crear_interfaz(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Configuración de Credenciales", font=("Arial", 14, "bold")).pack(pady=(0, 15))

        ctk.CTkLabel(frame, text="Google Gemini API Key:").pack(anchor="w")
        self.entry_api = ctk.CTkEntry(frame, width=300)
        self.entry_api.pack(pady=(0, 10))
        self.entry_api.insert(0, os.getenv("GOOGLE_API_KEY", ""))

        ctk.CTkLabel(frame, text="Email User (Gmail/Yahoo):").pack(anchor="w")
        self.entry_user = ctk.CTkEntry(frame, width=300)
        self.entry_user.pack(pady=(0, 10))
        self.entry_user.insert(0, os.getenv("EMAIL_USER", ""))

        ctk.CTkLabel(frame, text="Email Password (App Password):").pack(anchor="w")
        frame_pass = ctk.CTkFrame(frame, fg_color="transparent")
        frame_pass.pack(fill="x", pady=(0, 15))
        self.entry_pass = ctk.CTkEntry(frame_pass, width=260, show="*")
        self.entry_pass.pack(side="left", fill="x", expand=True)
        self.entry_pass.insert(0, os.getenv("EMAIL_PASS", ""))

        btn_eye = ctk.CTkButton(frame_pass, text="👁", width=35, command=self.toggle_pass, fg_color="#555", hover_color="#444")
        btn_eye.pack(side="right", padx=(5, 0))
        self.btn_eye = btn_eye

        # --- SECCIÓN DIRECTORIO ---
        ctk.CTkLabel(frame, text="Directorio de Informes:", font=("Arial", 10, "bold")).pack(anchor="center", pady=(10, 0))
        
        import config
        self.lbl_dir = ctk.CTkLabel(frame, text=str(config.DIRECTORIO_INFORMES), font=("Arial", 9), text_color="gray", wraplength=380, justify="center")
        self.lbl_dir.pack(pady=(0, 5), anchor="center")

        # --- BOTONES ---
        frame_botones = ctk.CTkFrame(frame, fg_color="transparent")
        frame_botones.pack(fill="x", pady=(5, 10))

        btn_selec = ctk.CTkButton(frame_botones, text="SELECCIONAR CARPETA", fg_color="#555", hover_color="#444", 
                      command=self.seleccionar_carpeta)
        btn_selec.pack(side="left", expand=True, fill="x", padx=5)
        ToolTip(btn_selec, "Carpeta en la que se guardará el material generado")

        ctk.CTkButton(frame_botones, text="SELECCIONAR MODELO IA", fg_color="#1F538D", 
                      command=self.abrir_selector_modelo).pack(side="left", expand=True, fill="x", padx=5)
        
        ctk.CTkButton(frame, text="GUARDAR CONF", fg_color="#2E7D32", command=self.guardar).pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text="El Bufón Semiótico: Una perla dentro de un diamante literario.\nUn proyecto co-creado entre Robel y Gemini", font=("Arial", 9, "italic"), text_color="gray").pack(pady=(10, 0))

    def toggle_pass(self):
        if self.entry_pass.cget("show") == "*":
            self.entry_pass.configure(show="")
            self.btn_eye.configure(text="🔒")
        else:
            self.entry_pass.configure(show="*")
            self.btn_eye.configure(text="👁")

    def seleccionar_carpeta(self):
        self.attributes("-topmost", False)
        ruta_elegida = filedialog.askdirectory()
        self.attributes("-topmost", True)
        self.lift()
        if ruta_elegida:
            import config
            ruta_final = Path(ruta_elegida) / "DataBufon"
            ruta_final.mkdir(parents=True, exist_ok=True)
            
            config.DIRECTORIO_INFORMES = ruta_final
            self.lbl_dir.configure(text=str(ruta_final))
            
            # Guardar en .env inmediatamente
            try:
                env_path = self.master_app.ruta_base / ".env"
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

    def abrir_selector_modelo(self):
        self.destroy()
        VentanaSelectorModelo(self.master_app)

    def guardar(self):
        v_api, v_user, v_pass = self.entry_api.get().strip(), self.entry_user.get().strip(), self.entry_pass.get().strip()
        
        import config
        v_model = config.MODELO_ACTUAL
        v_folder = str(config.DIRECTORIO_INFORMES)
        
        try:
            env_path = self.master_app.ruta_base / ".env"
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"GOOGLE_API_KEY={v_api}\n")
                f.write(f"EMAIL_USER={v_user}\n")
                f.write(f"EMAIL_PASS={v_pass}\n")
                f.write(f"GENAI_MODEL={v_model}\n")
                f.write(f"OUTPUT_FOLDER={v_folder}\n")
            
            actualizaciones = {
                "GOOGLE_API_KEY": v_api,
                "EMAIL_USER": v_user,
                "EMAIL_PASS": v_pass,
                "GENAI_MODEL": v_model,
                "OUTPUT_FOLDER": v_folder
            }
            os.environ.update(actualizaciones)
            
            # Actualizar config y recargar módulos en master_app
            config.API_KEY = v_api
            config.MAIL_USER = v_user
            config.MAIL_PASS = v_pass
            
            # Recargar instancias en la app principal
            from agente_ia import AgenteIA
            from gestor_email import GestorEmail
            self.master_app.agente_ia = AgenteIA()
            self.master_app.gestor_email = GestorEmail()

            self.master_app.verificar_estado_sistema()
            self.destroy()
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")


class VentanaSelectorModelo(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Seleccionar Modelo IA")
        w, h = 300, 420
        x = self.master_app.winfo_x() + (self.master_app.winfo_width() // 2) - (w // 2)
        y = self.master_app.winfo_y() + (self.master_app.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.attributes("-topmost", True)
        
        self.crear_interfaz()

    def crear_interfaz(self):
        ctk.CTkLabel(self, text="Modelos Disponibles", font=("Arial", 14, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(self, width=250, height=250)
        scroll.pack(pady=10, padx=10)
        
        import config
        self.var_modelo = ctk.StringVar(value=config.MODELO_ACTUAL)
        
        # Obtener modelos desde el agente (assumes api_ready)
        modelos = self.master_app.agente_ia.obtener_modelos_disponibles()
        
        for m in modelos:
            ctk.CTkRadioButton(scroll, text=m, variable=self.var_modelo, value=m).pack(anchor="w", pady=5, padx=5)

        ctk.CTkButton(self, text="GUARDAR CAMBIOS", command=self.guardar_modelo).pack(pady=10)
        ctk.CTkLabel(self, text="Algunos modelos podrían ser de pago", font=("Arial", 10), text_color="gray").pack(pady=(0, 10))

    def guardar_modelo(self):
        nuevo = self.var_modelo.get()
        import config
        config.MODELO_ACTUAL = nuevo
        try:
            env_path = self.master_app.ruta_base / ".env"
            lines = open(env_path).readlines() if env_path.exists() else []
            with open(env_path, "w") as f:
                found = False
                for l in lines:
                    if l.startswith("GENAI_MODEL="): f.write(f"GENAI_MODEL={nuevo}\n"); found = True
                    else: f.write(l)
                if not found: f.write(f"GENAI_MODEL={nuevo}\n")
            
            os.environ["GENAI_MODEL"] = nuevo
            self.master_app.lbl_modelo_actual_ui.configure(text=f"Modelo: {nuevo}")
            self.destroy()
            messagebox.showinfo("Modelo Actualizado", f"Se usará: {nuevo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")


class VentanaColoquio(ctk.CTkToplevel):
    def __init__(self, master, autor_nombre):
        super().__init__(master)
        self.master_app = master
        self.autor_nombre = autor_nombre
        
        self.title(f"Coloquio con {autor_nombre}")
        w, h = 600, 550
        x = self.master_app.winfo_x() + (self.master_app.winfo_width() // 2) - (w // 2)
        y = self.master_app.winfo_y() + (self.master_app.winfo_height() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        self.crear_interfaz()

    def crear_interfaz(self):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.chat_display = ctk.CTkTextbox(frame, state="disabled", font=("Consolas", 11), wrap="word")
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.progress_chat = ctk.CTkProgressBar(frame, height=5)
        self.progress_chat.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_chat.pack_forget()

        self._escribir_chat(f"--- Iniciando conversación con {self.autor_nombre} ---\n\n")
        
        # Recuperar historial previo si existe en master_app
        for a, m in self.master_app.historial_coloquio:
            n = self.autor_nombre if a == "Autor" else "Usted"
            self._escribir_chat(f"{n}: {m}\n\n")

        inp_frame = ctk.CTkFrame(self, height=50)
        inp_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.chat_entry = ctk.CTkEntry(inp_frame, placeholder_text="Escriba su mensaje...")
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.chat_entry.bind("<Return>", self._enviar_mensaje)
        
        ctk.CTkButton(inp_frame, text="ENVIAR", width=80, command=self._enviar_mensaje).pack(side="right", padx=5)
        
        ctk.CTkButton(self, text="CERRAR CONVERSACIÓN", fg_color="#444", hover_color="#333",
                      command=self.cerrar).pack(pady=(0, 10))

    def _escribir_chat(self, texto):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", texto)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _enviar_mensaje(self, event=None):
        msg = self.chat_entry.get().strip()
        if not msg: return
        self.chat_entry.delete(0, "end")
        
        self._escribir_chat(f"Usted: {msg}\n\n")
        self.master_app.historial_coloquio.append(("Usuario", msg))
        
        self.progress_chat.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_chat.start()
        
        threading.Thread(target=self._procesar_respuesta, args=(msg,), daemon=True).start()

    def _procesar_respuesta(self, msg_user):
        try:
            # Enviamos solo el nombre del autor, AgenteIA ya sabe qué hacer si fuera necesario reiniciar chat, 
            # pero aquí asumimos que chat_session ya está iniciada en master_app o la iniciamos si es None.
            # En gui.py original, se iniciaba antes de abrir ventana.
            # Aquí podemos asumir que chat_session existe en master_app.
            
            if not self.master_app.chat_session:
                 self.master_app.chat_session = self.master_app.agente_ia.iniciar_chat(self.autor_nombre)

            txt = self.master_app.agente_ia.enviar_mensaje(self.master_app.chat_session, msg_user)
            self.after(0, self._append_respuesta, txt)
            self.master_app.historial_coloquio.append(("Autor", txt))
        except Exception as e:
            err = str(e)
            m = "El autor está reflexionando profundamente..." if any(x in err for x in ["429", "Quota"]) else f"Error: {e}"
            self.after(0, self._append_respuesta, f"[{m}]")
        finally:
            self.progress_chat.stop()
            self.after(0, self.progress_chat.pack_forget)

    def _append_respuesta(self, txt):
        self.master_app.reporte_actual_guardado = False
        self._escribir_chat(f"{self.autor_nombre}: {txt}\n\n")

    def cerrar(self):
        self.destroy()
        self.master_app.ventana_coloquio = None
        
        if self.master_app.historial_coloquio:
             # Autosave al cerrar
             self.master_app._guardar_automatico(self.master_app.datos_json_actual, self.master_app.autor_actual)
             self.master_app._escribir_seguro(self.master_app.textbox, "\n[System]: Reporte actualizado con coloquio.\n")
