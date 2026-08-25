import tkinter as tk
from tkinter import Menu
from PIL import Image, ImageDraw, ImageFilter, ImageTk
import math
import os
import sys

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TAMANO = 170
VELOCIDAD = 2
INTERVALO_MS = 25
COLOR_TRANSPARENTE = "#00ff01"
PARPADEO_CADA = 120       # Aproximadamente cada 3 segundos
DURACION_PARPADEO = 5     # Aproximadamente 125 ms

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
        imagen = Image.open(ruta_recurso("peluche.png")).convert("RGBA")
        imagen.thumbnail((TAMANO, TAMANO), Image.Resampling.LANCZOS)
        imagen = self.agregar_contorno_uniforme(imagen)
        self.imagen_pil = imagen
        self.frames_normales = self.crear_frames_caminata(imagen)
        imagen_parpadeo = self.crear_imagen_parpadeo(imagen)
        self.frames_parpadeo = self.crear_frames_caminata(imagen_parpadeo)
        self.imagen_tk = self.frames_normales[1]

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
        self.parpadeando = False
        self.fin_parpadeo = 0

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

    def agregar_contorno_uniforme(self, imagen, grosor=3):
        """Genera un borde negro parejo a partir de la transparencia real."""
        alfa = imagen.getchannel("A")
        mascara_borde = alfa.filter(ImageFilter.MaxFilter(grosor * 2 + 1))
        contorno = Image.new("RGBA", imagen.size, (0, 0, 0, 0))
        contorno.putalpha(mascara_borde)
        contorno.alpha_composite(imagen)
        return contorno

    def evitar_halo_transparente(self, imagen):
        """Evita que el suavizado mezcle el borde con el verde transparente."""
        limpia = imagen.copy()
        alfa = limpia.getchannel("A").point(lambda valor: 255 if valor > 8 else 0)
        limpia.putalpha(alfa)
        return limpia

    def crear_frames_caminata(self, imagen):
        """Crea un ligero balanceo para simular pasos."""
        frames = []
        for angulo in (-2, 0, 2, 0):
            rotada = imagen.rotate(
                angulo,
                resample=Image.Resampling.BICUBIC,
                expand=False
            )
            rotada = self.evitar_halo_transparente(rotada)
            frames.append(ImageTk.PhotoImage(rotada))
        return frames

    def crear_imagen_parpadeo(self, imagen):
        """Cubre los ojos y dibuja una expresión de ojos cerrados."""
        parpadeo = imagen.copy()
        dibujo = ImageDraw.Draw(parpadeo)
        ancho, alto = imagen.size
        # Toma el tono directamente de la frente para integrarlo con la cara.
        color_cara = imagen.getpixel((ancho // 2, int(alto * 0.44)))
        color_linea = (28, 18, 15, 255)

        # Cajas proporcionales y simétricas para la ilustración actual.
        ojos = (
            (0.305, 0.365, 0.445, 0.555),
            (0.555, 0.365, 0.695, 0.555),
        )
        for px1, py1, px2, py2 in ojos:
            x1, y1 = int(ancho * px1), int(alto * py1)
            x2, y2 = int(ancho * px2), int(alto * py2)
            dibujo.ellipse((x1, y1, x2, y2), fill=color_cara)
            margen_x = max(2, int(ancho * 0.018))
            centro_y = int((y1 + y2) / 2)
            dibujo.arc(
                (x1 + margen_x, centro_y - 3, x2 - margen_x, centro_y + 8),
                start=10,
                end=170,
                fill=color_linea,
                width=max(2, int(ancho * 0.018))
            )
        return parpadeo

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
            salto = abs(math.sin(self.tick / 5.0)) * -4
            self.y = self.base_y + salto

            if not self.parpadeando and self.tick % PARPADEO_CADA == 0:
                self.parpadeando = True
                self.fin_parpadeo = self.tick + DURACION_PARPADEO
            elif self.parpadeando and self.tick >= self.fin_parpadeo:
                self.parpadeando = False

            paso = (self.tick // 5) % len(self.frames_normales)
            frames = self.frames_parpadeo if self.parpadeando else self.frames_normales
            self.imagen_tk = frames[paso]
            self.canvas.itemconfigure(self.id_img, image=self.imagen_tk)

            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

        self.root.after(INTERVALO_MS, self.mover)

if __name__ == "__main__":
    MascotaEscritorio()
