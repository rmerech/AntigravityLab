import tkinter as tk
import unicodedata
import re
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from typing import Optional

# ==============================================================================
# HERRAMIENTAS AUXILIARES - v0.9.7.6m
# ==============================================================================

class ToolTip(object):
    """ Clase auxiliar para crear 'Tooltips' (mensajes emergentes al pasar el mouse). """
    def __init__(self, widget, text='Información'):
        self.widget = widget
        self.text = text
        self.tipwindow: Optional[tk.Toplevel] = None
        self.id = None
        self.x = self.y = 0
        # [CORRECCIÓN v0.9.7.1] add='+' para evitar conflictos y binding agresivo
        self._id1 = self.widget.bind("<Enter>", self.enter, add="+")
        self._id2 = self.widget.bind("<Leave>", self.leave, add="+")
        self._id3 = self.widget.bind("<ButtonPress>", self.leave, add="+") # Ocultar al clicar

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id: self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.attributes("-topmost", True)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify='left',
                       background="#333333", fg="#D1D1D1",
                       relief='solid', borderwidth=1,
                       font=("Arial", 9, "normal"))
        label.pack(ipadx=5, ipady=3)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw: tw.destroy()

def limpiar_texto(texto):
    r"""
    Limpia una cadena de texto para que sea segura de usar como nombre de archivo en Windows.
    Windows prohíbe caracteres como: < > : " / \ | ? *
    """
    texto_sin_tildes = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[<>:"/\\|?*]', '', texto_sin_tildes).strip()

def poner_borde_inferior(parrafo):
    """
    [NUEVO v0.9.4] Función avanzada para manipular el XML de Word y agregar un borde inferior al párrafo.
    Esto permite un efecto de separación "Editorial" profesional.
    """
    p = parrafo._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')      # Grosor
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'auto')
    pBdr.append(bottom)
    pPr.append(pBdr)
