"""ALZA LA VOZ · que nadie se sienta solo.

Juego de acción contra el acoso escolar. Sam está en el centro y le llegan mensajes:
  - ACOSO (burbuja con picos): se frena disparando corazones con el clic.
  - APOYO (burbuja verde y redonda): se deja llegar, le sube el ánimo a Sam.
Con el IMPULSO lleno, Espacio = ¡Alza la voz! (onda que frena todo el acoso cercano).
Cada acción valiente hace que los testigos que solo miraban se sumen como aliados.

Archivos del proyecto:
  juego.py        este archivo: datos, lógica, dibujo y teclado
  estructuras.py  cola, pila, lista enlazada, lista circular, lista doble y multilista
  arte.py         librería de dibujos (personajes, burbujas, escenarios, iconos)
  datos/          textos.json (frases) y records.csv (mejores puntajes)
"""
import csv
import json
import math
import os
import random

import pygame

import arte
from estructuras import Cola, ListaCircular, ListaDoble, ListaEnlazada, Multilista, Pila

# ================================================================ 1. DATOS DEL JUEGO
ANCHO, ALTO = 1280, 720
SAM = pygame.Vector2(640, 410)
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
RUTA_TEXTOS = os.path.join(CARPETA, "textos.json")
RUTA_RECORDS = os.path.join(CARPETA, "records.csv")

# (lugar, frase del día, mensajes, segundos entre mensajes, velocidad, % de apoyo)
OLEADAS = [
    ("Llegada", "Hablar a tiempo frena el acoso.", 12, 1.6, 75, 35),
    ("Recreo", "Sin público, la burla pierde fuerza.", 14, 1.45, 82, 35),
    ("Almuerzo", "Nadie sobra: todos caben.", 16, 1.35, 88, 33),
    ("Pasillo", "Un rumor que no se pasa, se apaga.", 18, 1.25, 94, 32),
    ("Educación física", "La presión también te busca a ti.", 20, 1.15, 100, 30),
    ("Salida", "Mirar para otro lado no es neutral.", 22, 1.05, 106, 30),
    ("Chat de la noche", "Lo que pasa en el chat también duele.", 24, 0.95, 112, 28),
    ("Grupo de estudio", "Si duele, no es broma.", 26, 0.9, 118, 28),
    ("El Silencio", "Cuando uno alza la voz, otros se suman.", 28, 0.85, 122, 26),
    ("JEFE: El Chat del Salón", "Lo que se reenvía se multiplica.", 0, 0, 120, 30),  # jefe final
]
CONSEJOS = ["Di 'eso no da risa' y acércate a quien recibió la burla.",
            "Si te llega un rumor, no lo reenvíes. Ahí se apaga.",
            "Invita a quien está solo. Un 'vente' cambia un recreo."]
AYUDA_141 = "Si ves acoso, habla con un adulto de confianza. En Colombia: Línea 141 del ICBF, gratuita, 24 h."

COLORES = {  # paleta normal y de alto contraste (la forma también distingue: picos vs redondo)
    False: {"tinta": (255, 246, 229), "tinta2": (201, 195, 230), "voz": (255, 197, 61), "malo": (255, 77, 94),
            "malo_fondo": (58, 16, 32), "malo_txt": (255, 224, 228), "bueno": (46, 229, 157),
            "bueno_fondo": (217, 255, 238), "bueno_txt": (11, 59, 42), "aliado": (167, 139, 250),
            "jugador": (56, 214, 255), "gris": (138, 134, 160), "disfraz": (255, 233, 168)},
    True: {"tinta": (255, 255, 255), "tinta2": (220, 220, 220), "voz": (255, 230, 0), "malo": (255, 138, 0),
           "malo_fondo": (0, 0, 0), "malo_txt": (255, 255, 255), "bueno": (0, 220, 255),
           "bueno_fondo": (210, 250, 255), "bueno_txt": (0, 0, 0), "aliado": (255, 255, 255),
           "jugador": (255, 255, 255), "gris": (160, 160, 160), "disfraz": (255, 255, 120)},
}


# ================================================================ 2. ARCHIVOS
def cargar_frases():
    """Lee datos/textos.json y arma la multilista categoría → frases. Si el archivo falla, usa frases mínimas."""
    banco = Multilista()
    try:
        with open(RUTA_TEXTOS, encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        datos = {"malos": {"burla": ["Jaja, qué ridículo."]}, "buenos": {"apoyo": ["No estás solo."]}}
    for grupo in ("malos", "buenos"):
        for categoria, frases in datos.get(grupo, {}).items():
            for frase in frases:
                banco.agregar_frase(f"{grupo}:{categoria}", frase)
    return banco


def cargar_records():
    """Lee datos/records.csv (nombre, puntos). Las filas dañadas se ignoran."""
    records = []
    try:
        with open(RUTA_RECORDS, encoding="utf-8") as f:
            for fila in csv.reader(f):
                if len(fila) == 2 and fila[1].isdigit():
                    records.append((fila[0][:12], int(fila[1])))
    except (OSError, UnicodeDecodeError):
        pass
    return sorted(records, key=lambda r: -r[1])[:5]


def guardar_record(nombre, puntos):
    records = sorted(cargar_records() + [(nombre, puntos)], key=lambda r: -r[1])[:5]
    try:
        os.makedirs(CARPETA, exist_ok=True)
        with open(RUTA_RECORDS, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(records)
    except OSError:
        pass


# ================================================================ 3. SONIDO
def tono(frecuencia, duracion, volumen=0.25, deslizar=0.0):
    """Genera un sonido corto sin archivos de audio. Si no hay tarjeta de sonido, devuelve None."""
    try:
        muestras = int(22050 * duracion)
        datos = bytearray()
        for i in range(muestras):
            t = i / 22050
            f = frecuencia + deslizar * (i / muestras)
            v = int(volumen * 32767 * math.sin(2 * math.pi * f * t) * (1 - i / muestras))
            datos += v.to_bytes(2, "little", signed=True)
        return pygame.mixer.Sound(buffer=bytes(datos))
    except (pygame.error, ValueError):
        return None


# ================================================================ 4. PERSONAJES Y OBJETOS
class Mensaje:
    def __init__(self, texto, apoyo, angulo, velocidad):
        self.texto = texto
        self.apoyo = apoyo                     # True = apoyo (verde), False = acoso (picos)
        self.pos = SAM + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * 600
        self.inicio = pygame.Vector2(self.pos)  # para que la burbuja "aparezca" con un rebote
        self.velocidad = velocidad
        self.vivo = True
        self.w = self.h = 40                   # tamaño de la burbuja (se ajusta al dibujarla)


class Corazon:
    def __init__(self, pos, direccion, aliado=False):
        self.pos = pygame.Vector2(pos)
        self.vel = direccion * (520 if aliado else 640)
        self.aliado = aliado
        self.vivo = True


class Testigo:
    def __init__(self, i):
        angulo = math.radians(i * 45 + 22.5)
        self.i = i
        self.pos = SAM + pygame.Vector2(math.cos(angulo), math.sin(angulo)) * 260
        self.aliado = False
        self.t_disparo = random.random() * 3
        self.grito_t = 0.0


# ================================================================ 5. EL JUEGO
class Juego:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(22050, -16, 1)
        except pygame.error:
            pass
        pygame.display.set_caption("Alza la Voz")
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        F = pygame.font.SysFont
        self.f_logo = F("segoeuiblack,arialblack", 92)
        self.f_titulo = F("segoeuiblack,arialblack", 44)
        self.f_l = F("segoeui", 28, bold=True)
        self.f_m = F("segoeui", 21, bold=True)
        self.f_n = F("segoeuisemibold,segoeui", 19)
        self.f_s = F("segoeui", 17, bold=True)
        self.f_num = F("bahnschrift", 38, bold=True)
        self.sonidos = {"disparo": tono(900, 0.04, 0.06), "frenar": tono(660, 0.08), "apoyo": tono(1046, 0.18),
                        "golpe": tono(140, 0.15, 0.3), "voz": tono(220, 0.5, 0.35, 440), "testigo": tono(523, 0.3, 0.2, 520)}
        self.banco = cargar_frases()           # MULTILISTA
        self.records = cargar_records()        # ARCHIVO
        self.pantallas = Pila()                # PILA de pantallas
        self.pantallas.apilar("menu")
        self.contraste = False
        self.subtitulos = True
        self.panel_estructuras = False
        self.menu_sel = 0
        self.cache = {}
        self.subtitulo, self.subtitulo_t = "", 0.0
        self.nueva_partida()
        self.ir_al_menu()

    def ir_al_menu(self):
        self.pantallas.vaciar()
        self.pantallas.apilar("menu")
        self.en_partida = False

    @property
    def P(self):
        return COLORES[self.contraste]

    def sonar(self, nombre, subtitulo):
        s = self.sonidos.get(nombre)
        if s:
            s.play()
        if subtitulo and self.subtitulos:
            self.subtitulo, self.subtitulo_t = f"[{subtitulo}]", 1.4

    # ------------------------------------------------------------ partida
    def nueva_partida(self):
        self.animo = 100.0
        self.impulso = 0.0
        self.puntos = 0
        self.valentia = 0
        self.stats = {"frenados": 0, "apoyos": 0}
        self.jugador = pygame.Vector2(SAM.x, SAM.y + 130)
        self.t_disparo = 0.0
        self.mensajes = ListaEnlazada()        # LISTA ENLAZADA: mensajes en pantalla
        self.corazones = ListaEnlazada()       # LISTA ENLAZADA: corazones en pantalla
        self.textos = ListaEnlazada()          # avisos flotantes ("¡Frenado!")
        self.chispas = ListaEnlazada()         # partículas que saltan al frenar un mensaje
        self.t_golpe = self.t_apoyo = -9.0     # momento del último golpe y del último apoyo (animan a Sam)
        self.tiempo = 0.0
        self.buzon = ListaDoble()              # LISTA DOBLE: apoyos que llegaron a Sam
        self.testigos = ListaCircular()        # LISTA CIRCULAR: 8 testigos alrededor de Sam
        for i in range(8):
            self.testigos.agregar(Testigo(i))
        self.onda = None                       # radio de la onda de "¡Alza la voz!" (None = no hay)
        self.jefe = None
        self.resultado = ""
        self.nombre = ""
        self.oleada = 0
        self.siguiente_oleada()
        self.pantallas.vaciar()
        self.pantallas.apilar("juego")
        self.en_partida = True

    def siguiente_oleada(self):
        """Programa en una COLA todos los mensajes de la oleada: (segundo de llegada, es_apoyo, ángulo)."""
        self.oleada += 1
        lugar, frase, cantidad, cada, _vel, pct_apoyo = OLEADAS[self.oleada - 1]
        self.t_oleada = 0.0
        self.programados = Cola()
        for i in range(cantidad):
            self.programados.encolar((2.0 + i * cada, random.randint(1, 100) <= pct_apoyo,
                                      random.uniform(0, 2 * math.pi)))
        if lugar.startswith("JEFE: El Chat"):
            self.jefe = {"pos": pygame.Vector2(640, 190), "vida": 60, "vida_max": 60, "t": 1.0}
        self.banner = (f"OLEADA {self.oleada} · {lugar.replace('JEFE: ', '').upper()}", frase)
        self.banner_t = 3.0

    def crear_mensaje(self, apoyo, angulo, velocidad, pos=None):
        grupo = "buenos" if apoyo else "malos"
        categorias = [c for c, _n in self.banco.categorias() if c.startswith(grupo)]
        texto = self.banco.frase_al_azar(random.choice(categorias)) if categorias else "..."
        m = Mensaje(texto, apoyo, angulo, velocidad)
        if pos is not None:
            m.pos = pygame.Vector2(pos)
        self.mensajes.agregar(m)

    # ------------------------------------------------------------ acciones
    def avisar(self, texto, pos, color):
        self.textos.agregar({"texto": texto, "pos": pygame.Vector2(pos), "color": color, "vida": 1.0})

    def frenar(self, m):
        m.vivo = False
        self.stats["frenados"] += 1
        self.puntos += 100
        self.impulso = min(100, self.impulso + 6)
        self.sumar_valentia(1)
        self.avisar(random.choice(["¡Frenado!", "¡Respeto!", "¡Así no!"]), m.pos, self.P["voz"])
        for _ in range(12):
            self.chispas.agregar({"pos": pygame.Vector2(m.pos), "vida": 0.5,
                                  "vel": pygame.Vector2(random.uniform(-220, 220), random.uniform(-220, 220))})
        self.sonar("frenar", "frenado")

    def llega_apoyo(self, m):
        m.vivo = False
        self.stats["apoyos"] += 1
        self.animo = min(100, self.animo + 6)
        self.puntos += 50
        self.impulso = min(100, self.impulso + 8)
        self.sumar_valentia(2)
        self.buzon.agregar_final(m.texto)
        self.t_apoyo = self.tiempo
        self.avisar("¡Apoyo!", SAM + (0, -70), self.P["bueno"])
        self.sonar("apoyo", "campanita: llegó un apoyo")

    def golpe_a_sam(self, m):
        m.vivo = False
        self.animo -= 12
        self.t_golpe = self.tiempo
        self.avisar("Eso le dolió a Sam", SAM + (0, -70), self.P["malo"])
        self.sonar("golpe", "golpe a Sam")

    def disparo_a_apoyo(self, m):
        m.vivo = False
        self.puntos = max(0, self.puntos - 50)
        self.animo -= 8                              # Sam se queda sin ese apoyo: le duele
        self.impulso = max(0, self.impulso - 25)
        self.t_golpe = self.tiempo
        self.avisar("¡Ese era apoyo! Déjalo llegar.", m.pos, self.P["bueno"])
        self.sonar("golpe", "ese era un apoyo")

    def sumar_valentia(self, n):
        """Cada 10 puntos de valentía, el siguiente testigo del círculo que aún no ayuda se suma."""
        self.valentia += n
        aliados = sum(1 for t in self.testigos if t.aliado)
        while aliados < min(8, self.valentia // 10):
            t = self.testigos.siguiente_que_cumpla(lambda x: not x.aliado)
            if t is None:
                break
            t.aliado, t.grito_t = True, 1.8
            aliados += 1
            self.puntos += 200
            self.sonar("testigo", "un testigo se suma")

    def alza_la_voz(self):
        if self.impulso < 100:
            self.avisar("Aún no: llena el IMPULSO", self.jugador + (0, -50), self.P["tinta2"])
            return
        self.impulso = 0
        self.onda = 0.0
        self.sonar("voz", "¡ALZA LA VOZ!")
        self.avisar("¡ALZA LA VOZ!", self.jugador + (0, -70), self.P["voz"])

    # ------------------------------------------------------------ actualización (un cuadro)
    def actualizar(self, dt):
        self.t_oleada += dt
        self.tiempo += dt
        self.banner_t -= dt
        lugar, _f, _c, _cada, velocidad, pct_apoyo = OLEADAS[self.oleada - 1]

        # 1. COLA → LISTA: los mensajes cuyo segundo ya llegó pasan a la pantalla
        while not self.programados.vacia() and self.programados.ver_frente()[0] <= self.t_oleada:
            _t, apoyo, angulo = self.programados.desencolar()
            self.crear_mensaje(apoyo, angulo, velocidad)

        # 2. jugador: se mueve con WASD o flechas y dispara manteniendo el clic
        teclas = pygame.key.get_pressed()
        mov = pygame.Vector2((teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT]),
                             (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP]))
        if mov.length():
            self.jugador += mov.normalize() * 280 * dt
        self.jugador.x = max(30, min(ANCHO - 30, self.jugador.x))
        self.jugador.y = max(120, min(ALTO - 30, self.jugador.y))
        self.t_disparo -= dt
        if pygame.mouse.get_pressed()[0] and self.t_disparo <= 0:
            direccion = pygame.Vector2(pygame.mouse.get_pos()) - self.jugador
            if direccion.length():
                self.corazones.agregar(Corazon(self.jugador, direccion.normalize()))
                self.t_disparo = 0.16
                self.sonar("disparo", None)

        # 3. aliados: cada uno lanza un corazón al acoso más cercano a Sam
        cerca_de_sam = [m for m in self.mensajes if not m.apoyo and m.pos.distance_to(SAM) < 200]
        for t in self.testigos:
            t.grito_t -= dt
            if t.aliado:
                t.t_disparo -= dt
                if t.t_disparo <= 0 and cerca_de_sam:
                    objetivo = min(cerca_de_sam, key=lambda m: m.pos.distance_to(t.pos)).pos
                    self.corazones.agregar(Corazon(t.pos, (objetivo - t.pos).normalize(), aliado=True))
                    t.t_disparo = 3.5

        # 4. mover corazones y mensajes, y revisar choques
        for c in self.corazones:
            c.pos += c.vel * dt
        for m in self.mensajes:
            m.pos += (SAM - m.pos).normalize() * m.velocidad * dt
            for c in self.corazones:
                if c.vivo and m.vivo and abs(c.pos.x - m.pos.x) < m.w / 2 and abs(c.pos.y - m.pos.y) < m.h / 2:
                    c.vivo = False
                    if m.apoyo and not c.aliado:
                        self.disparo_a_apoyo(m)
                    elif not m.apoyo:
                        self.frenar(m)
            if m.vivo and m.pos.distance_to(SAM) < 50:
                self.llega_apoyo(m) if m.apoyo else self.golpe_a_sam(m)

        # 5. onda de "¡Alza la voz!": crece y frena todo el acoso que toca
        if self.onda is not None:
            self.onda += 1150 * dt
            for m in self.mensajes:
                if m.vivo and not m.apoyo and m.pos.distance_to(self.jugador) < self.onda:
                    self.frenar(m)
            if self.onda > 520:
                self.onda = None

        # 6. jefe final: lanza acoso desde la ventana del chat; los corazones le quitan vida
        if self.jefe:
            self.jefe["t"] -= dt
            if self.jefe["t"] <= 0:
                self.jefe["t"] = 0.75
                apoyo = random.randint(1, 100) <= pct_apoyo
                self.crear_mensaje(apoyo, 0, velocidad, pos=self.jefe["pos"] + (random.uniform(-120, 120), 70))
            caja = pygame.Rect(0, 0, 300, 170)
            caja.center = self.jefe["pos"]
            for c in self.corazones:
                if c.vivo and not c.aliado and caja.collidepoint(c.pos):
                    c.vivo = False
                    self.jefe["vida"] -= 1
                    self.puntos += 20
            if self.jefe["vida"] <= 0:
                self.jefe = None
                self.mensajes.eliminar_si(lambda m: not m.apoyo)
                self.terminar(True)
                return

        # 7. limpiar las listas: se borran los nodos que ya no sirven
        self.mensajes.eliminar_si(lambda m: not m.vivo)
        self.corazones.eliminar_si(lambda c: not c.vivo or not (0 <= c.pos.x <= ANCHO and 0 <= c.pos.y <= ALTO))
        for t in self.textos:
            t["vida"] -= dt
            t["pos"].y -= 30 * dt
        self.textos.eliminar_si(lambda t: t["vida"] <= 0)
        for c in self.chispas:
            c["vida"] -= dt
            c["pos"] += c["vel"] * dt
        self.chispas.eliminar_si(lambda c: c["vida"] <= 0)

        # 8. fin de oleada o de partida
        if self.animo <= 0:
            self.terminar(False)
        elif not self.jefe and self.programados.vacia() and self.mensajes.tam == 0:
            self.animo = min(100, self.animo + 10)
            self.siguiente_oleada()

    def terminar(self, victoria):
        self.resultado = "victoria" if victoria else "derrota"
        self.pantallas.apilar("final")

    # ================================================================ 6. DIBUJO
    def texto(self, s, fuente, color, x, y, centro=False, borde=False):
        img = arte.texto_borde(fuente, s, color) if borde else fuente.render(s, True, color)
        r = img.get_rect(center=(x, y)) if centro else img.get_rect(topleft=(x, y))
        self.pantalla.blit(img, r)
        return r

    def pastilla(self, s, x, y, fondo, color=(20, 14, 40)):
        img = self.f_s.render(s, True, color)
        r = img.get_rect(center=(x, y)).inflate(22, 8)
        pygame.draw.rect(self.pantalla, fondo, r, border_radius=r.h // 2)
        self.pantalla.blit(img, img.get_rect(center=r.center))

    def burbuja(self, m):
        """Superficie de la burbuja (en caché). Acoso: picos. Apoyo: verde y redonda."""
        clave = (m.texto, m.apoyo, self.contraste)
        if clave not in self.cache:
            palabras, lineas, linea = m.texto.split(), [], ""
            for p in palabras:                   # parte el texto en líneas de máximo 176 px
                prueba = (linea + " " + p).strip()
                if self.f_s.size(prueba)[0] > 176 and linea:
                    lineas.append(linea)
                    linea = p
                else:
                    linea = prueba
            lineas.append(linea)
            self.cache[clave] = arte.burbuja(lineas[:2], self.f_s, "bueno" if m.apoyo else "malo", self.P,
                                             "" if m.apoyo else "!", self.contraste)
        superficie, m.w, m.h = self.cache[clave]
        return superficie

    def dibujar_juego(self):
        P = self.P
        lugar = OLEADAS[self.oleada - 1][0]
        self.pantalla.blit(arte.escenario(lugar, self.contraste), (0, 0))
        if self.animo < 60 and not self.contraste:   # el mundo se enfría cuando Sam está mal
            self.pantalla.blit(arte.capa((20, 30, 90), (60 - self.animo) * 2.2), (0, 0))
        # testigos: grises si miran, morados si ya ayudan
        for t in self.testigos:
            if t.aliado:
                self.pantalla.blit(arte.halo(34, P["aliado"], 110), (t.pos.x - 34, t.pos.y - 30))
            else:
                self.pastilla("…", t.pos.x + 22, t.pos.y - 38, (70, 66, 96), (230, 228, 245))
            spr = arte.nino(46 if t.aliado else 54, P["aliado"] if t.aliado else (150, 146, 170), (59, 38, 24),
                            arte.PIELES[t.i % 6], t.i % 8, "grito" if t.grito_t > 0 else "feliz" if t.aliado else "preocupado",
                            apagado=not t.aliado)
            self.pantalla.blit(spr, spr.get_rect(midbottom=(t.pos.x, t.pos.y + 26)))
            if t.grito_t > 0:
                self.pastilla("¡Yo también te defiendo!", t.pos.x, t.pos.y - 50, P["aliado"])
        # Sam: su cara cambia según el ánimo; salta con un apoyo y tiembla en rojo con un golpe
        golpe = max(0.0, 0.45 - (self.tiempo - self.t_golpe)) / 0.45
        apoyo = max(0.0, 0.5 - (self.tiempo - self.t_apoyo)) / 0.5
        cara = "feliz" if self.animo > 70 or apoyo else "normal" if self.animo > 40 else "triste"
        cara = "triste" if golpe else cara
        aura = arte.mezclar((120, 130, 200), (255, 214, 140), self.animo / 100)
        self.pantalla.blit(arte.halo(110, aura, 110 + apoyo * 120), (SAM.x - 110, SAM.y - 120))
        sam = arte.nino(104, (255, 138, 61), (74, 44, 26), arte.PIELES[0], 0, cara, mochila=(88, 128, 232))
        r = sam.get_rect(midbottom=(SAM.x + math.sin(self.tiempo * 60) * 4 * golpe,
                                    SAM.y + 58 - math.sin(apoyo * math.pi) * 16))
        self.pantalla.blit(sam, r)
        if golpe:
            self.pantalla.blit(arte.tenido(sam, (255, 60, 80), 0.6 * golpe), r)
        self.pastilla("Sam", SAM.x, SAM.y + 74, (255, 138, 61))
        # jefe: ventana de chat
        if self.jefe:
            caja = pygame.Rect(0, 0, 300, 170)
            caja.center = self.jefe["pos"]
            arte.pegar_panel(self.pantalla, caja, color=(40, 26, 84), alfa=250, borde=P["malo"])
            self.texto("Chat del salón", self.f_m, P["tinta"], caja.x + 18, caja.y + 12)
            for i in range(3):
                pygame.draw.rect(self.pantalla, (70, 56, 120), (caja.x + 18, caja.y + 52 + i * 30, 160 + i * 30, 18),
                                 border_radius=9)
            pygame.draw.rect(self.pantalla, P["malo"], (caja.centerx - 50, caja.bottom - 34, 100, 26), border_radius=8)
            self.texto("Reenviar", self.f_s, (255, 255, 255), caja.centerx, caja.bottom - 21, centro=True)
        # mensajes, corazones y jugador
        for m in self.mensajes:
            s = self.burbuja(m)
            avance = m.inicio.distance_to(m.pos)           # la burbuja crece al salir del borde
            if avance < 45:
                s = pygame.transform.smoothscale_by(s, max(0.3, avance / 45))
            self.pantalla.blit(s, s.get_rect(center=m.pos))
        for c in self.corazones:
            color = P["aliado"] if c.aliado else P["voz"]
            estela = arte.corazon(5 if c.aliado else 7, arte.oscurecer(color, 0.35))
            self.pantalla.blit(estela, estela.get_rect(center=c.pos - c.vel * 0.025))
            img = arte.corazon(7 if c.aliado else 11, color)
            self.pantalla.blit(img, img.get_rect(center=c.pos))
        for c in self.chispas:
            pygame.draw.circle(self.pantalla, P["malo"], c["pos"], 2 + 6 * c["vida"])
        jug = arte.nino(66, P["jugador"], (36, 28, 56), arte.PIELES[3], 5, "grito" if pygame.mouse.get_pressed()[0] else "feliz")
        self.pantalla.blit(jug, jug.get_rect(midbottom=(self.jugador.x, self.jugador.y + 30)))
        apunta = pygame.Vector2(pygame.mouse.get_pos()) - self.jugador
        mega = arte.rotado(arte.megafono(38), -math.degrees(math.atan2(apunta.y, apunta.x)))
        self.pantalla.blit(mega, mega.get_rect(center=self.jugador + (apunta.normalize() * 30 if apunta.length() else (30, 0))))
        # onda de "¡Alza la voz!"
        if self.onda is not None:
            arte.onda_voz(self.pantalla, self.jugador, self.onda, P["voz"])
        if golpe and not self.contraste:
            self.pantalla.blit(arte.capa((255, 40, 70), 50 * golpe), (0, 0))
        for t in self.textos:
            self.texto(t["texto"], self.f_m, t["color"], t["pos"].x, t["pos"].y, centro=True, borde=True)
        self.dibujar_hud()

    def dibujar_hud(self):
        P = self.P
        arte.pegar_panel(self.pantalla, pygame.Rect(14, 10, 420, 86), color=(26, 20, 58), alfa=230)
        animo_cara = "feliz" if self.animo > 70 else "normal" if self.animo > 40 else "triste"
        sam = arte.cara(32, (255, 138, 61), (74, 44, 26), arte.PIELES[0], 0, animo_cara)
        self.pantalla.blit(sam, sam.get_rect(center=(54, 52)))
        self.texto("ÁNIMO DE SAM", self.f_s, P["tinta2"], 94, 16)
        color = P["bueno"] if self.animo > 60 else P["voz"] if self.animo > 30 else P["malo"]
        arte.barra(self.pantalla, pygame.Rect(94, 40, 260, 16), self.animo / 100, color)
        self.texto(str(int(max(0, self.animo))), self.f_m, P["tinta"], 364, 32)
        self.texto("IMPULSO", self.f_s, P["voz"] if self.impulso >= 100 else P["tinta2"], 94, 62)
        arte.barra(self.pantalla, pygame.Rect(184, 68, 170, 12), self.impulso / 100, P["voz"])
        if self.impulso >= 100:
            self.pantalla.blit(arte.halo(60, P["voz"], 70), (330, 2))
            self.pantalla.blit(arte.tecla(self.f_s, "Espacio", activa=True), (362, 60))
        self.texto(f"{self.puntos:,}".replace(",", "."), self.f_num, P["tinta"], 640, 30, centro=True, borde=True)
        for i, t in enumerate(self.testigos):    # una carita por testigo: gris mira, morada ayuda
            c = arte.cara(17, P["aliado"] if t.aliado else (150, 146, 170), (59, 38, 24), arte.PIELES[t.i % 6],
                          t.i % 8, "feliz" if t.aliado else "preocupado", apagado=not t.aliado)
            self.pantalla.blit(c, c.get_rect(center=(518 + i * 35, 92)))
        self.texto("TESTIGOS QUE SE SUMAN", self.f_s, P["tinta2"], 640, 66, centro=True)
        arte.pegar_panel(self.pantalla, pygame.Rect(ANCHO - 334, 10, 320, 86), color=(26, 20, 58), alfa=230)
        lugar = OLEADAS[self.oleada - 1][0].replace("JEFE: ", "")
        self.texto(f"OLEADA {self.oleada} DE 10", self.f_s, P["tinta2"], ANCHO - 316, 16)
        self.texto(lugar, self.f_m, P["tinta"], ANCHO - 316, 38)
        if self.jefe:
            arte.barra(self.pantalla, pygame.Rect(ANCHO - 316, 72, 280, 12), self.jefe["vida"] / self.jefe["vida_max"],
                       P["malo"])
        if self.banner_t > 0:
            caja = pygame.Rect(0, 0, 760, 100)
            caja.center = (640, 210)
            arte.pegar_panel(self.pantalla, caja, color=(30, 20, 66), alfa=240, borde=P["voz"])
            self.texto(self.banner[0], self.f_titulo, P["voz"], 640, 190, centro=True, borde=True)
            self.texto(self.banner[1], self.f_n, P["tinta"], 640, 238, centro=True)
        if self.subtitulo_t > 0 and self.subtitulos:
            self.pastilla(self.subtitulo, 640, ALTO - 20, (255, 240, 160))
        self.texto("P pausa · H ayuda · F2 estructuras", self.f_s, P["tinta2"], ANCHO - 300, ALTO - 30)
        if self.panel_estructuras:
            self.dibujar_estructuras()

    def dibujar_estructuras(self):
        """Modo profesor (F2): cuántos nodos tiene cada estructura en este momento."""
        caja = pygame.Rect(ANCHO - 420, 110, 400, 330)
        arte.pegar_panel(self.pantalla, caja, color=(12, 8, 30), alfa=240, borde=self.P["voz"])
        filas = [("PILA de pantallas", f"{self.pantallas.tam} (arriba: {self.pantallas.ver_tope()})"),
                 ("COLA de mensajes por llegar", f"{self.programados.tam} nodos"),
                 ("LISTA ENLAZADA de mensajes", f"{self.mensajes.tam} nodos"),
                 ("LISTA ENLAZADA de corazones", f"{self.corazones.tam} nodos"),
                 ("LISTA CIRCULAR de testigos", f"{sum(1 for t in self.testigos if t.aliado)} de 8 aliados"),
                 ("LISTA DOBLE buzón de Sam", f"{self.buzon.tam} apoyos"),
                 ("MULTILISTA de frases", f"{sum(1 for _ in self.banco.categorias())} categorías")]
        self.texto("MODO PROFESOR · estructuras (F2)", self.f_s, self.P["voz"], caja.x + 16, caja.y + 12)
        for i, (nombre, valor) in enumerate(filas):
            self.texto(nombre, self.f_s, self.P["aliado"], caja.x + 16, caja.y + 46 + i * 40)
            self.texto(valor, self.f_s, (255, 255, 255), caja.x + 16, caja.y + 64 + i * 40)

    def ventana(self, titulo, alto=520):
        """Fondo oscurecido y tarjeta central con título, para las pantallas de menú."""
        self.pantalla.blit(arte.desenfocado(self.pantalla), (0, 0))
        caja = pygame.Rect(0, 0, 960, alto)
        caja.center = (640, 370)
        arte.pegar_panel(self.pantalla, caja, color=(34, 26, 74), alfa=250)
        self.texto(titulo, self.f_titulo, self.P["voz"], 640, caja.y, centro=True, borde=True)
        return caja

    def dibujar_menu(self):
        P = self.P
        self.pantalla.blit(arte.escenario("menu", self.contraste), (0, 0))
        sam = arte.nino(150, (255, 138, 61), (74, 44, 26), arte.PIELES[0], 0, "feliz", mochila=(88, 128, 232))
        self.pantalla.blit(sam, sam.get_rect(midbottom=(930, 560)))
        for dx, estilo in ((-120, 2), (120, 3)):
            amigo = arte.nino(96, P["aliado"], (30, 30, 30), arte.PIELES[estilo], estilo, "feliz")
            self.pantalla.blit(amigo, amigo.get_rect(midbottom=(930 + dx, 560)))
        t = pygame.time.get_ticks() / 1000
        for i, (frase, apoyo, x, y) in enumerate((("¡Estoy contigo!", True, 760, 230), ("Nadie te invitó.", False, 1120, 190),
                                                  ("¿Te sientas con nosotros?", True, 1140, 330),
                                                  ("Jaja, qué ridículo.", False, 720, 330))):
            yy = y + math.sin(t * 1.4 + i) * 8
            s = self.burbuja(Mensaje(frase, apoyo, 0, 0))
            self.pantalla.blit(s, s.get_rect(center=(x, yy)))
            if not apoyo:   # un corazón vuela desde Sam hacia el acoso
                k = ((t * 0.6 + i * 0.3) % 1) * 0.75
                corazon = arte.corazon(10, P["voz"])
                self.pantalla.blit(corazon, corazon.get_rect(center=(930 + (x - 930) * k, 440 + (yy - 440) * k)))
        logo = arte.texto_degradado(self.f_logo, "ALZA LA VOZ", (255, 230, 140), (255, 150, 40))
        self.pantalla.blit(logo, logo.get_rect(center=(400, 120)))
        mega = arte.rotado(arte.megafono(58), 24)
        self.pantalla.blit(mega, mega.get_rect(center=(650, 70)))
        self.texto("Que nadie se sienta solo", self.f_l, P["tinta"], 400, 190, centro=True, borde=True)
        self.botones = []
        for i, (texto, _accion) in enumerate(self.opciones_menu()):
            r = pygame.Rect(0, 0, 360, 56)
            r.center = (400, 270 + i * 70)
            elegido = i == self.menu_sel
            pygame.draw.rect(self.pantalla, (10, 6, 26), r.move(0, 5), border_radius=16)
            pygame.draw.rect(self.pantalla, P["voz"] if elegido else (47, 37, 96), r, border_radius=16)
            if elegido:
                pygame.draw.rect(self.pantalla, (255, 255, 255), r, 3, border_radius=16)
            icono = arte.icono(("jugar", "como", "records", "salir")[i], 32, (36, 20, 6) if elegido else P["tinta"])
            self.pantalla.blit(icono, icono.get_rect(midleft=(r.x + 18, r.centery)))
            self.texto(texto, self.f_l, (36, 20, 6) if elegido else P["tinta"], r.centerx + 16, r.centery, centro=True)
            self.botones.append(r)
        self.texto("Flechas y Enter, o clic · F1 alto contraste", self.f_s, P["tinta2"], 400, 570, centro=True)
        self.pastilla(AYUDA_141, 640, ALTO - 28, P["bueno"])

    def opciones_menu(self):
        return [("JUGAR", "jugar"), ("Cómo jugar", "ayuda"), ("Récords", "records"), ("Salir", "salir")]

    def dibujar_ayuda(self):
        P = self.P
        caja = self.ventana("Cómo jugar")
        ejemplos = [Mensaje("Jaja, qué ridículo.", False, 0, 0), Mensaje("No estás solo.", True, 0, 0)]
        for i, (m, txt) in enumerate(zip(ejemplos, ["ACOSO: tiene picos. Frénalo con corazones.",
                                                    "APOYO: verde y redondo. Déjalo llegar a Sam."])):
            s = self.burbuja(m)
            self.pantalla.blit(s, s.get_rect(midleft=(caja.x + 40, caja.y + 80 + i * 80)))
            self.texto(txt, self.f_n, P["tinta"], caja.x + 300, caja.y + 68 + i * 80)
        lineas = ["Moverse: W A S D o flechas", "Lanzar corazones: mantener clic izquierdo",
                  "¡Alza la voz!: Espacio (con el impulso lleno)", "Pausa: P  ·  Ayuda: H  ·  Alto contraste: F1",
                  "Cada acción valiente suma testigos que te ayudan."]
        for i, linea in enumerate(lineas):
            self.texto(linea, self.f_n, P["tinta"], caja.x + 40, caja.y + 250 + i * 34)
        self.texto("Esc para volver", self.f_s, P["tinta2"], 640, caja.bottom - 30, centro=True)

    def dibujar_pausa(self):
        P = self.P
        caja = self.ventana("Pausa", alto=420)
        self.texto(f"Buzón de Sam: {self.buzon.tam} apoyos (← → para recorrer)", self.f_m, P["tinta"], 640,
                   caja.y + 70, centro=True)
        frase = self.buzon.valor_cursor()
        if frase:
            s = self.burbuja(Mensaje(frase, True, 0, 0))
            self.pantalla.blit(s, s.get_rect(center=(640, caja.y + 150)))
            self.texto(f"{self.buzon.posicion_cursor()} de {self.buzon.tam}", self.f_s, P["tinta2"], 640,
                       caja.y + 200, centro=True)
        self.texto("P continuar · Q volver al menú", self.f_m, P["voz"], 640, caja.y + 280, centro=True)
        self.pastilla(AYUDA_141, 640, caja.bottom - 40, P["bueno"])

    def dibujar_records(self):
        P = self.P
        caja = self.ventana("Récords", alto=440)
        if not self.records:
            self.texto("Aún no hay récords. ¡Juega una partida!", self.f_m, P["tinta"], 640, caja.y + 120, centro=True)
        for i, (nombre, puntos) in enumerate(self.records):
            self.texto(f"{i + 1}. {nombre}", self.f_l, P["tinta"], caja.x + 220, caja.y + 70 + i * 56)
            self.texto(str(puntos), self.f_l, P["voz"], caja.right - 300, caja.y + 70 + i * 56)
        self.texto("Esc para volver", self.f_s, P["tinta2"], 640, caja.bottom - 30, centro=True)

    def dibujar_final(self):
        P = self.P
        victoria = self.resultado == "victoria"
        self.pantalla.blit(arte.escenario("final" if victoria else "Pasillo", self.contraste), (0, 0))
        cara = "feliz" if victoria else "triste"
        if victoria:  # los testigos que se sumaron celebran con Sam
            for k, dx in enumerate((-190, -110, 110, 190)):
                amigo = arte.nino(90, P["aliado"], (30, 30, 30), arte.PIELES[k + 1], k + 1, "feliz")
                self.pantalla.blit(amigo, amigo.get_rect(midbottom=(300 + dx, 590)))
        sam = arte.nino(150, (255, 138, 61), (74, 44, 26), arte.PIELES[0], 0, cara, mochila=(88, 128, 232))
        self.pantalla.blit(sam, sam.get_rect(midbottom=(300, 600)))
        if victoria:
            arte.confeti(self.pantalla, pygame.time.get_ticks() / 1000)
        titulo = "SAM YA NO ESTÁ SOLO" if victoria else "ESTA VEZ, SAM SE SINTIÓ SOLO"
        self.texto(titulo, self.f_titulo, P["voz"] if victoria else (255, 170, 190), 640, 70, centro=True, borde=True)
        caja = pygame.Rect(600, 130, 620, 470)
        arte.pegar_panel(self.pantalla, caja, color=(30, 22, 66), alfa=245)
        y = caja.y + 30
        if not victoria:
            self.texto(random.Random(self.puntos).choice(CONSEJOS), self.f_n, P["bueno"], caja.x + 30, y)
            y += 50
        aliados = sum(1 for t in self.testigos if t.aliado)
        for nombre, valor in (("Puntos", self.puntos), ("Oleada", self.oleada), ("Mensajes frenados", self.stats["frenados"]),
                              ("Apoyos que llegaron", self.stats["apoyos"]), ("Testigos que se sumaron", aliados)):
            self.texto(nombre, self.f_n, P["tinta2"], caja.x + 30, y)
            self.texto(str(valor), self.f_m, P["tinta"], caja.right - 80, y)
            y += 40
        campo = pygame.Rect(caja.x + 30, caja.bottom - 130, caja.w - 60, 50)
        pygame.draw.rect(self.pantalla, P["voz"], campo, 3, border_radius=14)
        self.texto(f"Tu nombre: {self.nombre}|", self.f_m, P["tinta"], campo.x + 16, campo.y + 11)
        self.texto("Enter: guardar y jugar otra vez  ·  Esc: guardar y volver al menú", self.f_s, P["tinta2"],
                   caja.centerx, caja.bottom - 40, centro=True)

    def dibujar(self):
        pantalla = self.pantallas.ver_tope()
        if pantalla == "menu":
            self.dibujar_menu()
        elif pantalla == "final":
            self.dibujar_final()
        else:
            self.dibujar_juego() if self.en_partida else self.dibujar_menu()
            {"pausa": self.dibujar_pausa, "ayuda": self.dibujar_ayuda, "records": self.dibujar_records}.get(
                pantalla, lambda: None)()
        pygame.display.flip()

    # ================================================================ 7. TECLADO Y RATÓN
    def evento(self, e):
        pantalla = self.pantallas.ver_tope()
        if e.type == pygame.MOUSEBUTTONDOWN and pantalla == "menu":
            for i, r in enumerate(getattr(self, "botones", [])):
                if r.collidepoint(e.pos):
                    self.accion_menu(self.opciones_menu()[i][1])
            return
        if e.type == pygame.TEXTINPUT and pantalla == "final":
            for letra in e.text:   # entrada errada: solo letras, números y espacio, máximo 12
                if (letra.isalnum() or letra == " ") and len(self.nombre) < 12:
                    self.nombre += letra
            return
        if e.type != pygame.KEYDOWN:
            return
        k = e.key
        if k == pygame.K_F1:
            self.contraste = not self.contraste
            self.cache.clear()
        elif k == pygame.K_F2:
            self.panel_estructuras = not self.panel_estructuras
        elif pantalla == "menu":
            if k in (pygame.K_DOWN, pygame.K_s):
                self.menu_sel = (self.menu_sel + 1) % 4
            elif k in (pygame.K_UP, pygame.K_w):
                self.menu_sel = (self.menu_sel - 1) % 4
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                self.accion_menu(self.opciones_menu()[self.menu_sel][1])
        elif pantalla == "juego":
            if k == pygame.K_SPACE:
                self.alza_la_voz()
            elif k in (pygame.K_p, pygame.K_ESCAPE):
                self.pantallas.apilar("pausa")
            elif k == pygame.K_h:
                self.pantallas.apilar("ayuda")
            elif k not in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_UP, pygame.K_DOWN,
                           pygame.K_LEFT, pygame.K_RIGHT):
                self.avisar("Esa tecla no hace nada. Pulsa H para ver los controles.", self.jugador + (0, -60),
                            self.P["tinta2"])
        elif pantalla == "pausa":
            if k in (pygame.K_p, pygame.K_ESCAPE):
                self.pantallas.desapilar()       # PILA: volver = desapilar
            elif k == pygame.K_q:
                self.ir_al_menu()
            elif k == pygame.K_LEFT:
                self.buzon.anterior()            # LISTA DOBLE: hacia atrás
            elif k == pygame.K_RIGHT:
                self.buzon.siguiente()           # LISTA DOBLE: hacia adelante
        elif pantalla in ("ayuda", "records"):
            if k in (pygame.K_ESCAPE, pygame.K_h, pygame.K_BACKSPACE, pygame.K_RETURN):
                self.pantallas.desapilar()
        elif pantalla == "final":
            if k == pygame.K_BACKSPACE:
                self.nombre = self.nombre[:-1]
            elif k in (pygame.K_RETURN, pygame.K_ESCAPE):
                guardar_record(self.nombre.strip() or "Jugador", self.puntos)
                self.records = cargar_records()
                if k == pygame.K_RETURN:
                    self.nueva_partida()
                else:
                    self.ir_al_menu()

    def accion_menu(self, accion):
        if accion == "jugar":
            self.nueva_partida()
        elif accion == "salir":
            raise SystemExit
        else:
            self.pantallas.apilar(accion)

    def correr(self):
        pygame.key.start_text_input()
        while True:
            dt = min(self.reloj.tick(60) / 1000, 1 / 30)
            try:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        raise SystemExit
                    self.evento(e)
                self.subtitulo_t -= dt
                if self.pantallas.ver_tope() == "juego":
                    self.actualizar(dt)
                self.dibujar()
            except SystemExit:
                raise
            except Exception as error:  # un error nunca cierra el juego: se avisa y se vuelve al menú
                print("Error:", error)
                self.ir_al_menu()


if __name__ == "__main__":
    try:
        Juego().correr()
    except SystemExit:
        pygame.quit()
