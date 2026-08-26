import math
import os
import random
import sys
import time
import tkinter as tk
from tkinter import Menu

from PIL import Image, ImageDraw, ImageTk

TAMANO = 190
TAMANO_BALON = 74
VELOCIDAD = 2
INTERVALO_MS = 25
COLOR_TRANSPARENTE = "#010101"


def ruta_recurso(nombre):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, nombre)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)


class MascotaEscritorio:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Peluche 10")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.configurar_transparencia(self.root)

        self.ancho = TAMANO
        self.alto = TAMANO
        self.canvas = tk.Canvas(self.root, width=TAMANO, height=TAMANO, bg=COLOR_TRANSPARENTE, highlightthickness=0, bd=0)
        self.canvas.pack()

        imagen = Image.open(ruta_recurso("peluche_sin_circulo.png")).convert("RGBA")
        imagen.thumbnail((TAMANO - 8, TAMANO - 8), Image.Resampling.LANCZOS)
        sprite_llorando = Image.open(ruta_recurso("sprite_llorando_realista.png")).convert("RGBA")
        sprite_llorando.thumbnail((TAMANO - 8, TAMANO - 8), Image.Resampling.LANCZOS)
        sprite_enojado = Image.open(ruta_recurso("sprite_enojado_referencia.png")).convert("RGBA")
        sprite_enojado.thumbnail((TAMANO - 8, TAMANO - 8), Image.Resampling.LANCZOS)
        self.imagenes = {
            "normal": ImageTk.PhotoImage(imagen),
            "parpadeo": ImageTk.PhotoImage(self.crear_parpadeo(imagen)),
            "llorando": ImageTk.PhotoImage(sprite_llorando),
            "reganado": ImageTk.PhotoImage(sprite_enojado),
        }
        self.id_img = self.canvas.create_image(TAMANO // 2, TAMANO // 2, image=self.imagenes["normal"])

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.x = max(0, sw - TAMANO - 80)
        self.base_y = max(0, sh - TAMANO - 80)
        self.y = self.base_y
        self.dx = -VELOCIDAD
        self.tick = 0
        self.frames_salto = 0
        self.proximo_salto = 180
        self.frames_parpadeo = 0
        self.proximo_parpadeo = 70
        self.llorando_hasta = 0.0
        self.reganado_hasta = 0.0
        self.proximo_golpe = 0
        self.modo_juego = True
        self.pausado = False
        self.arrastrando = False
        self.drag_x = self.drag_y = 0
        self.ultimo_arrastre = None
        self.direccion_arrastre = 0
        self.sacudidas = 0
        self.ultima_sacudida = 0.0
        self.crear_balon()
        self.root.geometry(f"{TAMANO}x{TAMANO}+{int(self.x)}+{int(self.y)}")

        self.canvas.bind("<ButtonPress-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.terminar_arrastre)
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="Jugar con balon", command=self.jugar_con_balon)
        self.menu.add_command(label="Jugar / caminar solo", command=self.alternar_modo_juego)
        self.menu.add_command(label="Probar llanto", command=self.probar_llanto)
        self.menu.add_command(label="Probar enojo", command=self.probar_enojo)
        self.menu.add_command(label="Pausar / continuar", command=self.alternar_pausa)
        self.menu.add_command(label="Volver abajo", command=self.volver_abajo)
        self.menu.add_separator()
        self.menu.add_command(label="Cerrar mascota", command=self.cerrar)
        self.canvas.bind("<Button-3>", self.mostrar_menu)
        self.mover()
        self.root.mainloop()

    def configurar_transparencia(self, ventana):
        ventana.configure(bg=COLOR_TRANSPARENTE)
        try:
            ventana.wm_attributes("-transparentcolor", COLOR_TRANSPARENTE)
        except tk.TclError:
            pass

    def crear_balon(self):
        self.balon_root = tk.Toplevel(self.root)
        self.balon_root.overrideredirect(True)
        self.balon_root.attributes("-topmost", True)
        self.configurar_transparencia(self.balon_root)
        self.balon_canvas = tk.Canvas(self.balon_root, width=TAMANO_BALON, height=TAMANO_BALON, bg=COLOR_TRANSPARENTE, highlightthickness=0, bd=0)
        self.balon_canvas.pack()
        balon = Image.open(ruta_recurso("balon_peluche.png")).convert("RGBA")
        balon.thumbnail((TAMANO_BALON - 4, TAMANO_BALON - 4), Image.Resampling.LANCZOS)
        self.imagen_balon = ImageTk.PhotoImage(balon)
        self.balon_canvas.create_image(TAMANO_BALON // 2, TAMANO_BALON // 2, image=self.imagen_balon)
        self.arrastrando_balon = False
        self.balon_drag_x = 0
        self.balon_drag_y = 0
        self.balon_canvas.bind("<ButtonPress-1>", self.iniciar_arrastre_balon)
        self.balon_canvas.bind("<B1-Motion>", self.arrastrar_balon)
        self.balon_canvas.bind("<ButtonRelease-1>", self.terminar_arrastre_balon)
        self.balon_canvas.bind("<Double-Button-1>", self.patear_balon)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.balon_x = max(30, sw - 420)
        self.balon_y = sh - TAMANO_BALON - 55
        self.balon_dx, self.balon_dy = -4.0, 3.0
        self.balon_root.geometry(f"{TAMANO_BALON}x{TAMANO_BALON}+{int(self.balon_x)}+{int(self.balon_y)}")

    def coordenadas_ojos(self, imagen):
        ancho, alto = imagen.size
        return ancho, alto, int(alto * 0.455), int(ancho * 0.065)

    def crear_parpadeo(self, imagen):
        resultado = imagen.copy()
        dibujo = ImageDraw.Draw(resultado)
        ancho, _, y, radio = self.coordenadas_ojos(resultado)
        grosor = max(3, int(ancho * 0.018))
        for centro_x in (int(ancho * 0.40), int(ancho * 0.60)):
            dibujo.ellipse((centro_x - radio, y - radio, centro_x + radio, y + radio), fill="#fee7bd")
            dibujo.arc((centro_x - radio, y - radio // 3, centro_x + radio, y + radio // 2), 5, 175, fill="black", width=grosor)
        return resultado

    def iniciar_arrastre(self, event):
        self.arrastrando = True
        self.drag_x, self.drag_y = event.x, event.y
        self.ultimo_arrastre = (self.root.winfo_pointerx(), self.root.winfo_pointery(), time.monotonic())
        self.direccion_arrastre = 0
        self.sacudidas = 0

    def arrastrar(self, event):
        ahora, puntero_x, puntero_y = time.monotonic(), self.root.winfo_pointerx(), self.root.winfo_pointery()
        anterior_x, anterior_y, anterior_t = self.ultimo_arrastre
        cambio_x, cambio_y = puntero_x - anterior_x, puntero_y - anterior_y
        velocidad = math.hypot(cambio_x, cambio_y) / max(ahora - anterior_t, 0.001)
        direccion = 1 if (cambio_x if abs(cambio_x) >= abs(cambio_y) else cambio_y) >= 0 else -1
        if velocidad > 1800:
            if self.direccion_arrastre and direccion != self.direccion_arrastre and ahora - self.ultima_sacudida < 0.35:
                self.sacudidas += 1
            elif ahora - self.ultima_sacudida > 0.35:
                self.sacudidas = 0
            self.direccion_arrastre = direccion
            self.ultima_sacudida = ahora
            if self.sacudidas >= 2:
                self.llorando_hasta = ahora + 3.5
                self.sacudidas = 0
                self.actualizar_expresion(ahora)
        self.ultimo_arrastre = (puntero_x, puntero_y, ahora)
        self.x, self.y = puntero_x - self.drag_x, puntero_y - self.drag_y
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def terminar_arrastre(self, event):
        self.arrastrando = False
        self.base_y = self.y
        if self.en_esquina():
            # La esquina tiene prioridad: no debe llorar antes de enojarse.
            self.llorando_hasta = 0.0
            self.reganado_hasta = time.monotonic() + 7.0
            self.actualizar_expresion(time.monotonic())

    def en_esquina(self):
        margen, sw, sh = 150, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        return (self.x <= margen or self.x + TAMANO >= sw - margen) and (self.y <= margen or self.y + TAMANO >= sh - margen)

    def mostrar_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def alternar_pausa(self):
        self.pausado = not self.pausado

    def probar_llanto(self):
        self.reganado_hasta = 0.0
        self.llorando_hasta = time.monotonic() + 5.0
        self.actualizar_expresion(time.monotonic())

    def probar_enojo(self):
        self.llorando_hasta = 0.0
        self.reganado_hasta = time.monotonic() + 5.0
        self.actualizar_expresion(time.monotonic())

    def volver_abajo(self):
        self.base_y = max(0, self.root.winfo_screenheight() - TAMANO - 70)
        self.y = self.base_y

    def jugar_con_balon(self):
        self.modo_juego = True
        self.balon_root.deiconify()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.balon_x = random.randint(20, max(20, sw - TAMANO_BALON - 20))
        self.balon_y = random.randint(80, max(80, sh - TAMANO_BALON - 120))
        self.balon_dx = random.choice((-1, 1)) * random.randint(4, 7)
        self.balon_dy = random.choice((-1, 1)) * random.randint(3, 6)
        self.proximo_golpe = 0

    def alternar_modo_juego(self):
        self.modo_juego = not self.modo_juego
        if self.modo_juego:
            self.jugar_con_balon()
        else:
            self.arrastrando_balon = False
            self.balon_root.withdraw()
            self.dx = VELOCIDAD if self.dx >= 0 else -VELOCIDAD

    def patear_balon(self, event=None):
        self.balon_dx = 9 if self.balon_x < self.root.winfo_screenwidth() / 2 else -9
        self.balon_dy = -7.5

    def iniciar_arrastre_balon(self, event):
        self.arrastrando_balon = True
        self.balon_drag_x, self.balon_drag_y = event.x, event.y
        self.balon_dx = self.balon_dy = 0.0

    def arrastrar_balon(self, event):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.balon_x = min(sw - TAMANO_BALON, max(0, self.root.winfo_pointerx() - self.balon_drag_x))
        self.balon_y = min(sh - TAMANO_BALON, max(0, self.root.winfo_pointery() - self.balon_drag_y))
        self.balon_root.geometry(f"+{int(self.balon_x)}+{int(self.balon_y)}")

    def terminar_arrastre_balon(self, event):
        self.arrastrando_balon = False
        self.proximo_golpe = 0

    def actualizar_balon(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.balon_x += self.balon_dx
        self.balon_y += self.balon_dy
        if self.balon_x <= 0:
            self.balon_x, self.balon_dx = 0, abs(self.balon_dx)
        elif self.balon_x + TAMANO_BALON >= sw:
            self.balon_x, self.balon_dx = sw - TAMANO_BALON, -abs(self.balon_dx)
        if self.balon_y <= 0:
            self.balon_y, self.balon_dy = 0, abs(self.balon_dy)
        elif self.balon_y + TAMANO_BALON >= sh:
            self.balon_y, self.balon_dy = sh - TAMANO_BALON, -abs(self.balon_dy)
        self.balon_root.geometry(f"+{int(self.balon_x)}+{int(self.balon_y)}")

    def jugar_automaticamente(self):
        objetivo_x = self.balon_x - (TAMANO_BALON // 2)
        objetivo_y = self.balon_y - (TAMANO - TAMANO_BALON)
        distancia_x = objetivo_x - self.x
        distancia_y = objetivo_y - self.base_y
        balon_activo = self.arrastrando_balon or abs(self.balon_dx) > 0.25 or abs(self.balon_dy) > 0.25
        rapidez = 8 if balon_activo else 5

        if abs(distancia_x) > 6:
            self.dx = rapidez if distancia_x > 0 else -rapidez
        else:
            self.dx = 0

        # Sigue el balon tanto al subir como al bajar, no solo por el piso.
        paso_vertical = max(-rapidez, min(rapidez, distancia_y))
        self.base_y += paso_vertical
        self.base_y = max(0, min(self.root.winfo_screenheight() - TAMANO, self.base_y))

        cerca_del_balon = abs(distancia_x) < 92 and abs(distancia_y) < 100
        if cerca_del_balon and self.tick >= self.proximo_golpe:
            self.balon_dx = 10 if distancia_x > 0 else -10
            self.balon_dy = -7.5
            self.proximo_golpe = self.tick + 80

    def actualizar_expresion(self, ahora):
        if ahora < self.llorando_hasta:
            nombre = "llorando"
        elif ahora < self.reganado_hasta:
            nombre = "reganado"
        elif self.frames_parpadeo > 0:
            nombre = "parpadeo"
            self.frames_parpadeo -= 1
        else:
            nombre = "normal"
        self.canvas.itemconfigure(self.id_img, image=self.imagenes[nombre])

    def cerrar(self):
        self.balon_root.destroy()
        self.root.destroy()

    def mover(self):
        if not self.pausado and not self.arrastrando:
            sw = self.root.winfo_screenwidth()
            if self.modo_juego:
                self.jugar_automaticamente()
            self.x += self.dx
            if self.x <= 0:
                self.x, self.dx = 0, abs(self.dx)
            elif self.x + TAMANO >= sw:
                self.x, self.dx = sw - TAMANO, -abs(self.dx)
            self.tick += 1
            paso = abs(math.sin(self.tick / 5.0)) * 3
            if self.tick >= self.proximo_salto:
                self.frames_salto, self.proximo_salto = 0, self.tick + 220
            if self.frames_salto < 34 and self.tick >= self.proximo_salto - 220:
                salto = -math.sin((self.frames_salto / 33.0) * math.pi) * 34
                self.frames_salto += 1
            else:
                salto = 0
            self.y = self.base_y - paso + salto
            if self.tick >= self.proximo_parpadeo:
                self.frames_parpadeo, self.proximo_parpadeo = 14, self.tick + 85
            self.actualizar_expresion(time.monotonic())
            if self.modo_juego and not self.arrastrando_balon:
                self.actualizar_balon()
            self.root.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.root.after(INTERVALO_MS, self.mover)


if __name__ == "__main__":
    MascotaEscritorio()
