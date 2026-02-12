import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from config import MAIL_USER, MAIL_PASS, SMTP_SERVER, SMTP_PORT

# ==============================================================================
# GESTOR EMAIL - v0.9.8m
# ==============================================================================

class GestorEmail:
    """
    Clase que encapsula el envío de reportes por correo electrónico.
    """
    def __init__(self):
        pass

    def enviar_reporte(self, destinatarios_str, ruta_docx, ruta_pdf):
        """
        Envía el reporte y el PDF original a los destinatarios.
        Retorna True si es exitoso, lanza excepción si falla.
        """
        if not MAIL_USER or not MAIL_PASS:
            raise Exception("Credenciales de correo no configuradas.")

        lista_destinatarios = [m.strip() for m in destinatarios_str.split(',') if m.strip()]
        if not lista_destinatarios:
            raise Exception("Lista de destinatarios vacía.")

        try:
            # Configuración específica para Yahoo (como estaba en el original)
            # Si se desea hacer más genérico se podrían parametrizar servidor y puerto.
            servidor = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            servidor.starttls()
            servidor.login(str(MAIL_USER), str(MAIL_PASS))
            
            nombre_archivo_pdf = os.path.basename(ruta_pdf)
            nombre_archivo_docx = os.path.basename(ruta_docx) if ruta_docx else "Reporte.docx"

            for mail in lista_destinatarios:
                msg = MIMEMultipart()
                msg['From'] = str(MAIL_USER)
                msg['To'] = mail
                msg['Subject'] = f"Análisis: {nombre_archivo_pdf}"
                
                msg.attach(MIMEText("Adjunto encontrará el análisis solicitado.\n\nAtte,\nEl Bufón.", 'plain'))
                
                archivos_adjuntos = []
                if ruta_docx and os.path.exists(ruta_docx):
                    archivos_adjuntos.append(ruta_docx)
                if ruta_pdf and os.path.exists(ruta_pdf):
                    archivos_adjuntos.append(ruta_pdf)
                
                for fpath in archivos_adjuntos:
                    with open(fpath, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(fpath))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(fpath)}"'
                        msg.attach(part)
                
                servidor.send_message(msg)
            
            servidor.quit()
            return True

        except Exception as e:
            raise Exception(f"Error SMTP: {e}")
