import tkinter as tk
from tkinter import Menu
from PIL import Image, ImageDraw, ImageTk
import math
import os
import sys

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TAMANO = 190
VELOCIDAD = 2
INTERVALO_MS = 25
# Un negro casi puro evita el halo verde en los bordes semitransparentes.
COLOR_TRANSPARENTE = "#010101"

def ruta_recurso(nombre):
    """Funciona tanto en .py como si luego se convierte a .exe con PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, nombre)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)

class MascotaEscritorio:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Peluche 10")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # Transparencia para Windows
        self.root.configure(bg=COLOR_TRANSPARENTE)
        try:
            self.root.wm_attributes("-transparentcolor", COLOR_TRANSPARENTE)
        except tk.TclError:
            pass

        self.ancho = TAMANO
        self.alto = TAMANO

        self.canvas = tk.Canvas(
            self.root,
            width=self.ancho,
            height=self.alto,
            bg=COLOR_TRANSPARENTE,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack()

        # Cargar imagen
        imagen = Image.open(ruta_recurso("peluche_sin_circulo.png")).convert("RGBA")
        imagen.thumbnail((TAMANO - 8, TAMANO - 8), Image.Resampling.LANCZOS)
        self.imagen_pil = imagen
        self.imagen_tk = ImageTk.PhotoImage(imagen)
        self.imagen_parpadeo_tk = ImageTk.PhotoImage(self.crear_imagen_parpadeo(imagen))

        self.id_img = self.canvas.create_image(
            TAMANO // 2,
            TAMANO // 2,
            image=self.imagen_tk
        )

        # Posición inicial
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.x = max(0, sw - self.ancho - 80)
        self.base_y = max(0, sh - self.alto - 80)
        self.y = self.base_y
        self.dx = -VELOCIDAD
        self.tick = 0
        self.frames_salto = 0
        self.proximo_salto = 180
        self.frames_parpadeo = 0
        self.proximo_parpadeo = 70

        self.pausado = False
        self.arrastrando = False
        self.drag_x = 0
        self.drag_y = 0

        self.root.geometry(f"{self.ancho}x{self.alto}+{self.x}+{self.y}")

        # Arrastrar con clic izquierdo
        self.canvas.bind("<ButtonPress-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.terminar_arrastre)

        # Menú clic derecho
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="Pausar / continuar", command=self.alternar_pausa)
        self.menu.add_command(label="Volver abajo", command=self.volver_abajo)
        self.menu.add_separator()
        self.menu.add_command(label="Cerrar mascota", command=self.root.destroy)

        self.canvas.bind("<Button-3>", self.mostrar_menu)

        self.mover()
        self.root.mainloop()

    def iniciar_arrastre(self, event):
        self.arrastrando = True
        self.drag_x = event.x
        self.drag_y = event.y

    def arrastrar(self, event):
        nuevo_x = self.root.winfo_pointerx() - self.drag_x
        nuevo_y = self.root.winfo_pointery() - self.drag_y
        self.x = nuevo_x
        self.y = nuevo_y
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def terminar_arrastre(self, event):
        self.arrastrando = False
        self.base_y = self.y

    def mostrar_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def alternar_pausa(self):
        self.pausado = not self.pausado

    def volver_abajo(self):
        sh = self.root.winfo_screenheight()
        self.base_y = max(0, sh - self.alto - 70)
        self.y = self.base_y

    def crear_imagen_parpadeo(self, imagen):
        """Crea un fotograma con los ojos cerrados sin alterar el PNG original."""
        parpadeo = imagen.copy()
        dibujo = ImageDraw.Draw(parpadeo)
        ancho, alto = parpadeo.size
        y = int(alto * 0.455)
        grosor = max(3, int(ancho * 0.018))
        for centro_x in (int(ancho * 0.40), int(ancho * 0.60)):
            radio = int(ancho * 0.065)
            dibujo.ellipse(
                (centro_x - radio, y - radio, centro_x + radio, y + radio),
                fill="#fee7bd",
            )
            dibujo.arc(
                (centro_x - radio, y - radio // 3, centro_x + radio, y + radio // 2),
                start=5,
                end=175,
                fill="black",
                width=grosor,
            )
        return parpadeo

    def mover(self):
        if not self.pausado and not self.arrastrando:
            sw = self.root.winfo_screenwidth()

            self.x += self.dx

            # Rebota al llegar a los bordes
            if self.x <= 0:
                self.x = 0
                self.dx = abs(self.dx)
            elif self.x + self.ancho >= sw:
                self.x = sw - self.ancho
                self.dx = -abs(self.dx)

            # Pequeño movimiento arriba/abajo para darle vida
            self.tick += 1
            paso = abs(math.sin(self.tick / 5.0)) * 3

            if self.tick >= self.proximo_salto:
                self.frames_salto = 0
                self.proximo_salto = self.tick + 220

            if self.frames_salto < 34 and self.tick >= self.proximo_salto - 220:
                progreso = self.frames_salto / 33.0
                salto = -math.sin(progreso * math.pi) * 34
                self.frames_salto += 1
            else:
                salto = 0

            self.y = self.base_y - paso + salto

            if self.tick >= self.proximo_parpadeo:
                self.frames_parpadeo = 14
                self.proximo_parpadeo = self.tick + 85
            if self.frames_parpadeo > 0:
                self.canvas.itemconfigure(self.id_img, image=self.imagen_parpadeo_tk)
                self.frames_parpadeo -= 1
            else:
                self.canvas.itemconfigure(self.id_img, image=self.imagen_tk)

            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

        self.root.after(INTERVALO_MS, self.mover)

if __name__ == "__main__":
    MascotaEscritorio()
