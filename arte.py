"""Kit de arte de Alza la Voz: todo se dibuja por código y se guarda en caché.

Los sprites se dibujan al triple de tamaño y se reducen con suavizado (supermuestreo), así
los bordes salen limpios sin usar imágenes externas. Este módulo no conoce la lógica del juego.
"""
import math
import random

import pygame

SS = 3  # factor de supermuestreo
_cache = {}

TINTA_OSCURA = (22, 16, 44)        # contorno tipo "sticker"
PIELES = [(255, 219, 184), (240, 190, 150), (214, 160, 120), (170, 118, 84), (128, 86, 60), (250, 205, 170)]


# ------------------------------------------------------------------ color
def mezclar(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def aclarar(c, k):
    return mezclar(c, (255, 255, 255), k)


def oscurecer(c, k):
    return mezclar(c, (0, 0, 0), k)


def gris(c, k=0.82):
    g = int(c[0] * 0.3 + c[1] * 0.5 + c[2] * 0.2)
    return mezclar(c, (g * 0.75 + 30, g * 0.72 + 28, g * 0.8 + 48), k)


# ------------------------------------------------------------------ superficies base
def degradado(w, h, arriba, abajo, medio=None):
    """Degradado vertical: se pintan 2 o 3 píxeles y se escalan con suavizado."""
    cols = [arriba, medio, abajo] if medio else [arriba, abajo]
    s = pygame.Surface((1, len(cols)))
    for i, c in enumerate(cols):
        s.set_at((0, i), c)
    return pygame.transform.smoothscale(s, (w, h))


def halo(radio, color, alfa=255, potencia=2.0):
    """Luz radial suave (alfa que cae hacia el borde). Se calcula pequeña y se escala."""
    clave = ("halo", radio, color, alfa, potencia)
    if clave not in _cache:
        n = 48
        s = pygame.Surface((n * 2, n * 2), pygame.SRCALPHA)
        for r in range(n, 0, -1):
            a = int(alfa * (1 - r / n) ** potencia)
            pygame.draw.circle(s, (*color, a), (n, n), r)
        _cache[clave] = pygame.transform.smoothscale(s, (radio * 2, radio * 2))
    return _cache[clave]


def vineta(w, h, fuerza=150):
    clave = ("vineta", w, h, fuerza)
    if clave not in _cache:
        n = 64
        s = pygame.Surface((n, n), pygame.SRCALPHA)
        for y in range(n):
            for x in range(n):
                d = math.hypot((x - n / 2) / (n / 2), (y - n / 2) / (n / 2))
                s.set_at((x, y), (8, 4, 20, int(fuerza * max(0.0, min(1.0, (d - 0.55) / 0.75)) ** 1.6)))
        _cache[clave] = pygame.transform.smoothscale(s, (w, h))
    return _cache[clave]


def suave(w, h, dibujar):
    """Crea una superficie w×h dibujando a SS× y reduciendo con suavizado."""
    g = pygame.Surface((int(w * SS), int(h * SS)), pygame.SRCALPHA)
    dibujar(g, SS)
    return pygame.transform.smoothscale(g, (int(w), int(h)))


def rect_r(s, col, r, radio, ancho=0):
    pygame.draw.rect(s, col, r, ancho, border_radius=int(radio))


# ------------------------------------------------------------------ corazón
def _pts_corazon(cx, cy, r, n=40):
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 16, cy + y * r / 16))
    return pts


def corazon(r, color, borde=True, brillo=True):
    """Corazón con contorno y brillo. r = radio aproximado en px."""
    clave = ("corazon", r, color, borde, brillo)
    if clave not in _cache:
        lado = int(r * 2.6) + 4

        def d(g, k):
            c = lado * k / 2
            if borde:
                pygame.draw.polygon(g, TINTA_OSCURA, _pts_corazon(c, c - k * 0.2, (r + 2.2) * k))
            pygame.draw.polygon(g, color, _pts_corazon(c, c - k * 0.2, r * k))
            if brillo:
                pygame.draw.ellipse(g, aclarar(color, 0.65), (c - r * 0.62 * k, c - r * 0.72 * k, r * 0.5 * k, r * 0.34 * k))

        _cache[clave] = suave(lado, lado, d)
    return _cache[clave]


def estrella(r, color, puntas=5):
    clave = ("estrella", r, color, puntas)
    if clave not in _cache:
        lado = int(r * 2.4) + 4

        def d(g, k):
            c = lado * k / 2
            pts = [(c + (r if i % 2 == 0 else r * 0.45) * k * math.cos(i * math.pi / puntas - math.pi / 2),
                    c + (r if i % 2 == 0 else r * 0.45) * k * math.sin(i * math.pi / puntas - math.pi / 2))
                   for i in range(puntas * 2)]
            pygame.draw.polygon(g, color, pts)

        _cache[clave] = suave(lado, lado, d)
    return _cache[clave]


# ------------------------------------------------------------------ personajes
def _pelo(g, k, estilo, col, cx, cy, r):
    """Peinados sobre una cabeza de centro (cx, cy) y radio r (ya escalados)."""
    osc = oscurecer(col, 0.25)
    if estilo == 2:  # afro
        for dx, dy, rr in ((-0.75, -0.35, 0.55), (0.75, -0.35, 0.55), (-0.4, -0.85, 0.6), (0.4, -0.85, 0.6),
                           (0, -1.0, 0.62), (-0.95, 0.1, 0.42), (0.95, 0.1, 0.42)):
            pygame.draw.circle(g, col, (cx + dx * r, cy + dy * r), rr * r)
    elif estilo == 3:  # largo
        pygame.draw.rect(g, col, (cx - r * 1.08, cy - r * 0.5, r * 2.16, r * 1.75), border_radius=int(r * 0.5))
    elif estilo == 4:  # dos moñitos
        pygame.draw.circle(g, col, (cx - r * 0.95, cy - r * 0.8), r * 0.42)
        pygame.draw.circle(g, col, (cx + r * 0.95, cy - r * 0.8), r * 0.42)
    # casquete común (media elipse superior)
    casco = pygame.Rect(cx - r * 1.06, cy - r * 1.12, r * 2.12, r * 1.5)
    pygame.draw.ellipse(g, col, casco)
    if estilo == 5:  # puntas
        for i in range(5):
            x0 = cx - r * 0.9 + i * r * 0.45
            pygame.draw.polygon(g, col, [(x0 - r * 0.2, cy - r * 0.75), (x0 + r * 0.25, cy - r * 0.75),
                                         (x0 + r * 0.1, cy - r * 1.42)])
    elif estilo == 6:  # rizos
        for i in range(6):
            pygame.draw.circle(g, col, (cx - r * 0.85 + i * r * 0.34, cy - r * 0.88 - (i % 2) * r * 0.12), r * 0.3)
    elif estilo == 7:  # gorro
        pygame.draw.ellipse(g, osc, (cx - r * 1.12, cy - r * 0.62, r * 2.24, r * 0.5))
        pygame.draw.circle(g, aclarar(col, 0.5), (cx, cy - r * 1.18), r * 0.2)
    return osc


def nino(tam, camiseta, pelo, piel, estilo=0, expresion="normal", apagado=False, mochila=None):
    """Personaje de cuerpo entero estilo 'sticker'. tam = alto en píxeles."""
    clave = ("nino", tam, camiseta, pelo, piel, estilo, expresion, apagado, mochila)
    if clave in _cache:
        return _cache[clave]
    if apagado:
        camiseta, pelo, piel = gris(camiseta), gris(pelo, 0.7), gris(piel, 0.6)
        mochila = gris(mochila) if mochila else None
    w, h = tam * 0.92, tam * 1.1

    def d(g, k):
        u = tam * k / 100
        cx = w * k / 2
        linea = max(1, int(2.6 * u))
        borde = TINTA_OSCURA
        pant = (52, 46, 92) if not apagado else (60, 56, 84)
        # sombra en el piso
        sombra = pygame.Surface((int(60 * u), int(14 * u)), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (8, 4, 20, 90), sombra.get_rect())
        g.blit(sombra, (cx - 30 * u, 96 * u))
        # --- contorno (todas las formas un poco más grandes, en tinta)
        e = 2.6 * u
        if mochila:
            rect_r(g, borde, (cx - 26 * u - e, 56 * u - e, 52 * u + 2 * e, 30 * u + 2 * e), 12 * u)
        rect_r(g, borde, (cx - 19 * u - e, 54 * u - e, 38 * u + 2 * e, 36 * u + 2 * e), 15 * u)
        for sx in (-1, 1):
            pygame.draw.circle(g, borde, (cx + sx * 23 * u, 66 * u), 8 * u + e)
            pygame.draw.circle(g, borde, (cx + sx * 25 * u, 77 * u), 6 * u + e)
            rect_r(g, borde, (cx + sx * 9.5 * u - 6.5 * u - e, 84 * u - e, 13 * u + 2 * e, 17 * u + 2 * e), 6 * u)
        pygame.draw.circle(g, borde, (cx, 34 * u), 27 * u + e)
        # --- mochila, piernas, cuerpo y brazos
        if mochila:
            rect_r(g, mochila, (cx - 26 * u, 56 * u, 52 * u, 30 * u), 12 * u)
        for sx in (-1, 1):
            rect_r(g, pant, (cx + sx * 9.5 * u - 6.5 * u, 84 * u, 13 * u, 13 * u), 5 * u)
            rect_r(g, aclarar(borde, 0.25), (cx + sx * 9.5 * u - 7.5 * u, 95 * u, 15 * u, 6.5 * u), 3 * u)
        rect_r(g, camiseta, (cx - 19 * u, 54 * u, 38 * u, 36 * u), 15 * u)
        rect_r(g, oscurecer(camiseta, 0.16), (cx - 19 * u, 78 * u, 38 * u, 12 * u), 10 * u)
        rect_r(g, aclarar(camiseta, 0.22), (cx - 13 * u, 57 * u, 12 * u, 9 * u), 5 * u)
        for sx in (-1, 1):
            pygame.draw.circle(g, camiseta, (cx + sx * 23 * u, 66 * u), 8 * u)
            pygame.draw.circle(g, piel, (cx + sx * 25 * u, 77 * u), 6 * u)
        # --- cabeza
        cy, r = 34 * u, 27 * u
        if estilo in (2, 3, 4):
            _pelo_atras = pygame.Surface(g.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(g, piel, (cx, cy), r)
        pygame.draw.circle(g, oscurecer(piel, 0.1), (cx, cy + r * 0.62), r * 0.5)
        pygame.draw.circle(g, piel, (cx, cy + r * 0.45), r * 0.62)
        # pelo: se dibuja y luego se "recorta" la cara con una elipse de piel
        _pelo(g, k, estilo, pelo, cx, cy, r)
        cara = pygame.Rect(cx - r * 0.86, cy - r * 0.42, r * 1.72, r * 1.4)
        pygame.draw.ellipse(g, piel, cara)
        if estilo == 1:  # flequillo de lado
            pygame.draw.polygon(g, pelo, [(cx - r * 0.95, cy - r * 0.5), (cx + r * 0.6, cy - r * 0.62),
                                          (cx - r * 0.2, cy - r * 0.05), (cx - r * 0.9, cy + r * 0.05)])
        # --- cara
        ojo_y = cy + 3 * u
        oscuro = (40, 26, 50)
        triste = expresion in ("triste", "preocupado")
        if expresion == "feliz":
            for sx in (-1, 1):
                pygame.draw.arc(g, oscuro, (cx + sx * 10 * u - 5 * u, ojo_y - 4 * u, 10 * u, 9 * u), 0.25, math.pi - 0.25,
                                max(2, int(2.6 * u)))
        else:
            for sx in (-1, 1):
                dy = 1.6 * u if expresion == "triste" else 0
                pygame.draw.ellipse(g, oscuro, (cx + sx * 10 * u - 3.4 * u, ojo_y - 4.6 * u + dy, 6.8 * u, 9.2 * u))
                pygame.draw.circle(g, (255, 255, 255), (cx + sx * 10 * u - 1.1 * u, ojo_y - 2.4 * u + dy), 1.7 * u)
        if triste:
            for sx in (-1, 1):
                pygame.draw.line(g, oscuro, (cx + sx * 15 * u, ojo_y - 8 * u), (cx + sx * 6 * u, ojo_y - 11.5 * u), linea)
        # mejillas
        mej = pygame.Surface((int(10 * u), int(6 * u)), pygame.SRCALPHA)
        pygame.draw.ellipse(mej, (255, 120, 130, 0 if apagado else 120), mej.get_rect())
        g.blit(mej, (cx - 21 * u, cy + 9 * u))
        g.blit(mej, (cx + 11 * u, cy + 9 * u))
        # boca
        by = cy + 15 * u
        boca = (150, 50, 70) if not apagado else (90, 80, 100)
        if expresion == "feliz":
            pygame.draw.ellipse(g, boca, (cx - 8 * u, by - 5 * u, 16 * u, 13 * u))
            pygame.draw.rect(g, piel, (cx - 9 * u, by - 6 * u, 18 * u, 6.5 * u))
            pygame.draw.ellipse(g, (255, 150, 160), (cx - 4 * u, by + 3 * u, 8 * u, 4.5 * u))
        elif expresion == "grito":
            pygame.draw.ellipse(g, boca, (cx - 6 * u, by - 3 * u, 12 * u, 12 * u))
            pygame.draw.ellipse(g, (255, 150, 160), (cx - 3.4 * u, by + 3.4 * u, 6.8 * u, 4.4 * u))
        elif expresion == "normal":
            pygame.draw.arc(g, boca, (cx - 7 * u, by - 6 * u, 14 * u, 11 * u), math.pi + 0.35, 2 * math.pi - 0.35, linea)
        elif expresion == "preocupado":
            pygame.draw.line(g, boca, (cx - 5 * u, by + 3 * u), (cx + 5 * u, by + 2 * u), linea)
        else:  # triste
            pygame.draw.arc(g, boca, (cx - 7 * u, by + 0.5 * u, 14 * u, 11 * u), 0.4, math.pi - 0.4, linea)
            pygame.draw.polygon(g, (120, 200, 255), [(cx + 12 * u, ojo_y + 5 * u), (cx + 9.6 * u, ojo_y + 10.5 * u),
                                                     (cx + 14.4 * u, ojo_y + 10.5 * u)])
            pygame.draw.circle(g, (120, 200, 255), (cx + 12 * u, ojo_y + 11 * u), 2.5 * u)

    _cache[clave] = suave(w, h, d)
    return _cache[clave]


def megafono(largo, color=(255, 201, 77)):
    """Megáfono apuntando a la derecha; se rota hacia donde apunta el jugador."""
    clave = ("megafono", largo, color)
    if clave not in _cache:
        w, h = largo, largo * 0.8

        def d(g, k):
            L, H = w * k, h * k
            cy = H / 2
            cuerpo = [(L * 0.18, cy - H * 0.12), (L * 0.86, cy - H * 0.42), (L * 0.86, cy + H * 0.42), (L * 0.18, cy + H * 0.12)]
            gordo = [(x + (-2.5 * k if x < L / 2 else 2.5 * k), y + (-2.5 * k if y < cy else 2.5 * k)) for x, y in cuerpo]
            pygame.draw.polygon(g, TINTA_OSCURA, gordo)
            rect_r(g, TINTA_OSCURA, (L * 0.02, cy - H * 0.16, L * 0.2, H * 0.32), 3 * k)
            pygame.draw.polygon(g, color, cuerpo)
            pygame.draw.polygon(g, aclarar(color, 0.45), [cuerpo[0], cuerpo[1], (L * 0.86, cy - H * 0.2), (L * 0.18, cy - H * 0.04)])
            rect_r(g, (255, 255, 255), (L * 0.83, cy - H * 0.46, L * 0.11, H * 0.92), 3 * k)
            rect_r(g, oscurecer(color, 0.3), (L * 0.05, cy - H * 0.11, L * 0.15, H * 0.22), 2 * k)

        _cache[clave] = suave(w, h, d)
    return _cache[clave]


def rotado(sprite, angulo_grados, paso=6):
    """Rotación cacheada por pasos de 'paso' grados."""
    a = int(round(angulo_grados / paso) * paso) % 360
    clave = ("rot", id(sprite), a)
    if clave not in _cache:
        _cache[clave] = pygame.transform.rotozoom(sprite, a, 1)
    return _cache[clave]


# ------------------------------------------------------------------ burbujas de mensaje
def _dentado(r, paso, amp):
    """Contorno con dientes regulares alrededor de un rectángulo (el acoso tiene picos)."""
    pts = []
    nx = max(2, int(r.w / paso))
    ny = max(2, int(r.h / paso))
    for i in range(nx * 2):
        pts.append((r.left + r.w * i / (nx * 2), r.top - (amp if i % 2 else 0)))
    for i in range(ny * 2):
        pts.append((r.right + (amp if i % 2 else 0), r.top + r.h * i / (ny * 2)))
    for i in range(nx * 2):
        pts.append((r.right - r.w * i / (nx * 2), r.bottom + (amp if i % 2 else 0)))
    for i in range(ny * 2):
        pts.append((r.left - (amp if i % 2 else 0), r.bottom - r.h * i / (ny * 2)))
    return pts


def burbuja(lineas, fuente, tipo, P, glifo="", contraste=False):
    """tipo: 'bueno', 'malo', 'disfraz' o 'gris'. Devuelve (superficie, ancho_cuerpo, alto_cuerpo)."""
    clave = ("burbuja", tuple(lineas), tipo, glifo, contraste, id(fuente))
    if clave in _cache:
        return _cache[clave]
    alto_l = fuente.get_linesize() - 2
    tw = max(fuente.size(l)[0] for l in lineas)
    w, h = tw + 44, len(lineas) * alto_l + 16
    m = 14  # margen para brillo, sombra y picos

    def d(g, k):
        r = pygame.Rect(m * k, m * k, w * k, h * k)
        if tipo == "bueno":
            if not contraste:
                for i, a in enumerate((26, 44, 70)):
                    rect_r(g, (*P["bueno"], a), r.inflate((10 - i * 3) * k, (10 - i * 3) * k), h * k)
            rect_r(g, (8, 4, 20, 110), r.move(0, 3 * k), h * k)
            rect_r(g, P["bueno"], r.inflate(5 * k, 5 * k), h * k)
            rect_r(g, P["bueno_fondo"], r, h * k)
            rect_r(g, (255, 255, 255, 130), (r.x + 10 * k, r.y + 3 * k, r.w - 20 * k, 5 * k), 3 * k)
        elif tipo == "gris":
            rect_r(g, (70, 66, 92), r.inflate(4 * k, 4 * k), h * k)
            rect_r(g, P["gris"], r, h * k)
        else:
            fondo = P["disfraz"] if tipo == "disfraz" else P["malo_fondo"]
            pts = _dentado(r, 11 * k, 6 * k)
            sombra = [(x, y + 4 * k) for x, y in pts]
            pygame.draw.polygon(g, (8, 4, 20, 120), sombra)
            pygame.draw.polygon(g, P["malo"], _dentado(r.inflate(5 * k, 5 * k), 11 * k, 7 * k))
            pygame.draw.polygon(g, fondo, pts)
            if tipo == "disfraz":  # borde roto: trozos del color de fondo tapan el borde
                for i in range(0, r.w, 22 * k):
                    pygame.draw.rect(g, (0, 0, 0, 0), (r.x + i, r.y - 12 * k, 8 * k, 9 * k))
                    pygame.draw.rect(g, (0, 0, 0, 0), (r.x + i + 11 * k, r.bottom + 3 * k, 8 * k, 9 * k))
            elif not contraste:
                rect_r(g, (*aclarar(P["malo_fondo"], 0.14), 255), (r.x + 4 * k, r.y + 3 * k, r.w - 8 * k, r.h * 0.45), 6 * k)
        # insignia
        cx, cy = r.x + 15 * k, r.centery
        if tipo == "bueno":
            pygame.draw.circle(g, P["bueno"], (cx, cy), 11 * k)
            pygame.draw.polygon(g, (255, 255, 255), _pts_corazon(cx, cy, 6.2 * k))
        elif tipo == "gris":
            pygame.draw.circle(g, (70, 66, 92), (cx, cy), 10 * k)
        else:
            pygame.draw.circle(g, (224, 164, 40) if tipo == "disfraz" else P["malo"], (cx, cy), 11 * k)

    s = suave(w + 2 * m, h + 2 * m, d)
    txt = {"bueno": P["bueno_txt"], "gris": (40, 40, 52), "disfraz": (70, 36, 0)}.get(tipo, P["malo_txt"])
    for i, l in enumerate(lineas):
        s.blit(fuente.render(l, True, txt), (m + 32, m + 8 + i * alto_l))
    if glifo and tipo in ("malo", "disfraz"):
        gi = fuente.render(glifo, True, (255, 255, 255))
        s.blit(gi, gi.get_rect(center=(m + 15, m + h // 2)))
    _cache[clave] = (s, w, h)
    return _cache[clave]


# ------------------------------------------------------------------ texto con contorno
def texto_borde(fuente, txt, color, borde=TINTA_OSCURA, grosor=3, sombra=None):
    clave = ("txtb", id(fuente), txt, color, borde, grosor, sombra)
    if clave not in _cache:
        base = fuente.render(txt, True, color)
        w, h = base.get_size()
        extra = grosor + (4 if sombra else 0)
        s = pygame.Surface((w + 2 * extra, h + 2 * extra), pygame.SRCALPHA)
        if sombra:
            sh = fuente.render(txt, True, sombra)
            for dx in range(-grosor, grosor + 1, max(1, grosor // 2)):
                for dy in range(-grosor, grosor + 1, max(1, grosor // 2)):
                    s.blit(sh, (extra + dx + 3, extra + dy + 4))
        b = fuente.render(txt, True, borde)
        pasos = 16
        for i in range(pasos):
            a = 2 * math.pi * i / pasos
            s.blit(b, (extra + math.cos(a) * grosor, extra + math.sin(a) * grosor))
        s.blit(base, (extra, extra))
        _cache[clave] = s
        if len(_cache) > 4000:  # los textos flotantes cambian mucho: se limpia para no crecer sin fin
            for c in [c for c in _cache if c[0] == "txtb"][:1500]:
                del _cache[c]
    return _cache[clave]


def texto_degradado(fuente, txt, arriba, abajo, borde=TINTA_OSCURA, grosor=5, sombra=(255, 107, 90)):
    """Para el logotipo: relleno en degradado, contorno y sombra desplazada."""
    clave = ("txtg", id(fuente), txt, arriba, abajo, borde, grosor, sombra)
    if clave not in _cache:
        mascara = fuente.render(txt, True, (255, 255, 255))
        w, h = mascara.get_size()
        relleno = degradado(w, h, arriba, abajo).convert_alpha()
        relleno.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        extra = grosor + 8
        s = pygame.Surface((w + 2 * extra, h + 2 * extra), pygame.SRCALPHA)
        sh = fuente.render(txt, True, sombra)
        b = fuente.render(txt, True, borde)
        for i in range(20):
            a = 2 * math.pi * i / 20
            s.blit(sh, (extra + math.cos(a) * grosor + 5, extra + math.sin(a) * grosor + 7))
        for i in range(20):
            a = 2 * math.pi * i / 20
            s.blit(b, (extra + math.cos(a) * grosor, extra + math.sin(a) * grosor))
        s.blit(relleno, (extra, extra))
        _cache[clave] = s
    return _cache[clave]


# ------------------------------------------------------------------ piezas de interfaz
def panel(w, h, color=(30, 24, 62), alfa=225, radio=22, borde=(120, 104, 190), brillo=True):
    """Tarjeta de 'vidrio': sombra, cuerpo translúcido, borde y brillo superior."""
    clave = ("panel", w, h, color, alfa, radio, borde, brillo)
    if clave not in _cache:
        m = 14

        def d(g, k):
            r = pygame.Rect(m * k, m * k, w * k, h * k)
            for i, a in enumerate((18, 30, 46)):
                rect_r(g, (4, 2, 14, a), r.move(0, 5 * k).inflate((8 - i * 3) * k, (8 - i * 3) * k), radio * k)
            rect_r(g, (*color, alfa), r, radio * k)
            if brillo:  # reflejo fino en el borde superior (sin franja a media altura)
                rect_r(g, (255, 255, 255, 34), (r.x + radio * k * 0.6, r.y + 2 * k, r.w - radio * k * 1.2, 3 * k), 2 * k)
            if borde:
                rect_r(g, (*borde, 200), r, radio * k, max(1, int(1.6 * k)))

        _cache[clave] = (suave(w + 2 * m, h + 2 * m, d), m)
    return _cache[clave]


def pegar_panel(dest, rect, **kw):
    s, m = panel(rect.w, rect.h, **kw)
    dest.blit(s, (rect.x - m, rect.y - m))


def barra(dest, rect, frac, color, fondo=(46, 38, 84), radio=None, brillo=True):
    radio = rect.h // 2 if radio is None else radio
    pygame.draw.rect(dest, (10, 6, 26), rect.inflate(4, 4), border_radius=radio + 2)
    pygame.draw.rect(dest, fondo, rect, border_radius=radio)
    w = int(rect.w * max(0.0, min(1.0, frac)))
    if w > 2:
        r = pygame.Rect(rect.x, rect.y, max(w, rect.h), rect.h)
        pygame.draw.rect(dest, color, r, border_radius=radio)
        if brillo and rect.h >= 8:
            pygame.draw.rect(dest, aclarar(color, 0.4), (r.x + 4, r.y + 2, max(0, r.w - 8), max(2, rect.h // 4)),
                             border_radius=radio)


def tecla(fuente, txt, activa=False):
    """Tecla dibujada (para las ayudas de control)."""
    clave = ("tecla", id(fuente), txt, activa)
    if clave not in _cache:
        tw, th = fuente.size(txt)
        w, h = max(th + 12, tw + 18), th + 10

        def d(g, k):
            rect_r(g, (10, 6, 26), (0, 3 * k, w * k, h * k), 7 * k)
            rect_r(g, (255, 201, 77) if activa else (236, 230, 255), (0, 0, w * k, h * k), 7 * k)
            rect_r(g, (255, 255, 255), (3 * k, 2 * k, (w - 6) * k, 5 * k), 3 * k)

        s = suave(w, h + 3, d)
        t = fuente.render(txt, True, (30, 22, 60))
        s.blit(t, t.get_rect(center=(w // 2, h // 2)))
        _cache[clave] = s
    return _cache[clave]


def interruptor(encendido, color=(59, 229, 138)):
    clave = ("sw", encendido, color)
    if clave not in _cache:
        def d(g, k):
            rect_r(g, color if encendido else (74, 66, 112), (0, 0, 58 * k, 30 * k), 15 * k)
            x = 43 if encendido else 15
            pygame.draw.circle(g, (10, 6, 26), (x * k, 16 * k), 12 * k)
            pygame.draw.circle(g, (255, 255, 255), (x * k, 15 * k), 11 * k)

        _cache[clave] = suave(58, 30, d)
    return _cache[clave]


# ------------------------------------------------------------------ iconos de cartas
def icono(nombre, tam, color):
    """Iconos de trazo grueso para las cartas y los botones."""
    clave = ("icono", nombre, tam, color)
    if clave in _cache:
        return _cache[clave]

    def d(g, k):
        u = tam * k / 48
        t = max(2, int(3.4 * u))
        L = lambda pts, cerrado=False: pygame.draw.lines(g, color, cerrado, [(x * u, y * u) for x, y in pts], t)
        C = lambda x, y, r, ancho=0: pygame.draw.circle(g, color, (x * u, y * u), r * u, 0 if not ancho else t)
        A = lambda x, y, w, h, a0, a1: pygame.draw.arc(g, color, (x * u, y * u, w * u, h * u), a0, a1, t)
        mega = lambda dx=0: (pygame.draw.polygon(g, color, [((7 + dx) * u, 20 * u), ((14 + dx) * u, 20 * u),
                                                           ((28 + dx) * u, 11 * u), ((28 + dx) * u, 37 * u),
                                                           ((14 + dx) * u, 28 * u), ((7 + dx) * u, 28 * u)]))
        if nombre in ("voz", "megafono", "jugar"):
            mega()
            A(26, 15, 14, 18, -1.0, 1.0)
            if nombre != "jugar":
                A(26, 9, 22, 30, -1.0, 1.0)
            if nombre == "megafono":
                L([(40, 6), (36, 14), (42, 14), (38, 22)])
        elif nombre == "rapidas":
            rect_r(g, color, (16 * u, 12 * u, 26 * u, 18 * u), 6 * u, t)
            L([(22, 30), (20, 37), (28, 30)])
            for y in (16, 22, 28):
                L([(3, y), (11, y)])
        elif nombre == "paso":
            for x, y in ((15, 14), (32, 26)):
                pygame.draw.ellipse(g, color, ((x - 6) * u, (y - 9) * u, 12 * u, 18 * u))
                rect_r(g, color, ((x - 5) * u, (y + 11) * u, 10 * u, 5 * u), 2 * u)
        elif nombre == "escuchar":
            A(12, 6, 24, 26, -0.6, math.pi + 0.2)
            L([(32, 24), (27, 31), (27, 37)])
            A(15, 31, 12, 10, math.pi, 2 * math.pi)
            A(19, 13, 10, 10, -0.4, math.pi)
        elif nombre == "coro":
            for x, y, r in ((24, 27, 11), (10, 15, 6), (38, 15, 6)):
                pygame.draw.polygon(g, color, _pts_corazon(x * u, y * u, r * u))
        elif nombre == "noreenviar":
            L([(9, 31), (9, 24), (15, 19), (33, 19)])
            L([(27, 11), (35, 19), (27, 27)])
            L([(8, 42), (40, 6)])
        elif nombre == "profe":
            C(24, 12, 7)
            rect_r(g, color, (11 * u, 22 * u, 26 * u, 22 * u), 9 * u)
            rect_r(g, TINTA_OSCURA, (26 * u, 28 * u, 8 * u, 10 * u), 2 * u)
        elif nombre == "contagio":
            pts = [(24 + (16 if i % 2 == 0 else 7) * math.cos(i * math.pi / 5 - math.pi / 2),
                    21 + (16 if i % 2 == 0 else 7) * math.sin(i * math.pi / 5 - math.pi / 2)) for i in range(10)]
            pygame.draw.polygon(g, color, [(x * u, y * u) for x, y in pts])
            L([(9, 43), (15, 37)])
            L([(39, 43), (33, 37)])
            L([(24, 45), (24, 40)])
        elif nombre == "amigo":
            for x in (14, 34):
                C(x, 14, 6.5)
                rect_r(g, color, ((x - 9) * u, 23 * u, 18 * u, 19 * u), 8 * u)
            L([(19, 30), (29, 30)])
        elif nombre == "circulo":
            for i in range(10):
                a = i * math.pi / 5
                A(6, 6, 36, 36, a, a + 0.38)
            pygame.draw.polygon(g, color, _pts_corazon(24 * u, 24 * u, 8 * u))
        elif nombre == "red":
            nodos = [(24, 9), (9, 35), (39, 35), (24, 26)]
            for a, b in ((0, 3), (1, 3), (2, 3), (0, 1), (0, 2), (1, 2)):
                L([nodos[a], nodos[b]])
            for x, y in nodos:
                C(x, y, 5)
        elif nombre == "practica":
            C(24, 24, 17, 1)
            C(24, 24, 9, 1)
            C(24, 24, 3)
        elif nombre == "como":
            C(24, 24, 18, 1)
            A(17, 11, 14, 14, -0.5, math.pi)
            L([(24, 25), (24, 29)])
            C(24, 35, 2.4)
        elif nombre == "mural":
            pygame.draw.polygon(g, color, _pts_corazon(24 * u, 23 * u, 17 * u))
        elif nombre == "records":
            rect_r(g, color, (14 * u, 7 * u, 20 * u, 20 * u), 8 * u)
            A(5, 9, 14, 13, math.pi / 2, 3 * math.pi / 2)
            A(29, 9, 14, 13, -math.pi / 2, math.pi / 2)
            L([(24, 27), (24, 36)])
            rect_r(g, color, (14 * u, 36 * u, 20 * u, 6 * u), 2 * u)
        elif nombre == "ajustes":
            for y, x in ((13, 30), (24, 16), (35, 27)):
                L([(7, y), (41, y)])
                C(x, y, 5.5)
        elif nombre == "quehacer":
            pygame.draw.polygon(g, color, [(24 * u, 5 * u), (40 * u, 11 * u), (40 * u, 24 * u), (24 * u, 43 * u),
                                           (8 * u, 24 * u), (8 * u, 11 * u)])
            pygame.draw.polygon(g, TINTA_OSCURA, _pts_corazon(24 * u, 21 * u, 8 * u))
        elif nombre == "salir":
            rect_r(g, color, (9 * u, 8 * u, 20 * u, 32 * u), 4 * u, t)
            L([(22, 24), (41, 24)])
            L([(34, 17), (41, 24), (34, 31)])
        elif nombre == "candado":
            A(16, 8, 16, 20, 0, math.pi)
            rect_r(g, color, (12 * u, 21 * u, 24 * u, 19 * u), 4 * u)
        elif nombre == "pausa":
            rect_r(g, color, (13 * u, 10 * u, 8 * u, 28 * u), 3 * u)
            rect_r(g, color, (27 * u, 10 * u, 8 * u, 28 * u), 3 * u)

    _cache[clave] = suave(tam, tam, d)
    return _cache[clave]


# ------------------------------------------------------------------ escenarios
# nombre, cielo arriba, cielo medio, cielo abajo, color de siluetas, color del piso, motivo
LUGARES = {
    "Llegada":            ((44, 36, 98), (126, 78, 140), (255, 164, 120), (36, 28, 76), (58, 46, 104), "colegio"),
    "Recreo":             ((24, 70, 110), (40, 120, 130), (120, 190, 140), (20, 62, 80), (36, 104, 108), "patio"),
    "Almuerzo":           ((70, 36, 80), (140, 70, 80), (236, 150, 90), (58, 30, 66), (104, 56, 78), "mesas"),
    "Pasillo":            ((30, 40, 100), (52, 64, 140), (96, 110, 190), (26, 32, 82), (46, 56, 122), "casilleros"),
    "JEFE: El Chat del Salón": ((36, 20, 80), (70, 34, 120), (130, 60, 150), (30, 16, 66), (56, 30, 100), "chat"),
    "Educación física":   ((20, 84, 120), (40, 130, 140), (250, 170, 90), (18, 66, 92), (34, 110, 120), "cancha"),
    "Salida":             ((60, 30, 100), (190, 70, 110), (255, 170, 80), (46, 24, 76), (120, 54, 96), "reja"),
    "Chat de la noche":   ((10, 12, 44), (22, 26, 78), (50, 44, 120), (8, 10, 34), (20, 22, 66), "noche"),
    "Grupo de estudio":   ((50, 34, 60), (104, 66, 70), (200, 140, 90), (40, 26, 50), (84, 54, 66), "libros"),
    "JEFE: El Silencio":  ((8, 6, 20), (16, 10, 36), (30, 18, 56), (6, 4, 16), (14, 10, 32), "vacio"),
    "menu":               ((34, 28, 92), (120, 70, 140), (255, 170, 110), (30, 24, 74), (52, 42, 100), "colegio"),
    "final":              ((70, 50, 120), (220, 120, 110), (255, 214, 120), (56, 40, 96), (120, 80, 110), "colegio"),
}


def _siluetas(g, k, motivo, col, W, H, rng):
    """Formas simples del lugar, casi del mismo color del fondo para no competir con el juego."""
    R = lambda x, y, w, h, c=col, rad=0: pygame.draw.rect(g, c, (x * k, y * k, w * k, h * k), border_radius=int(rad * k))
    claro = aclarar(col, 0.1)
    luz = (255, 220, 140)
    base = H - 96
    if motivo == "colegio":
        R(380, base - 150, 520, 250)
        R(560, base - 210, 160, 70)
        pygame.draw.polygon(g, col, [(540 * k, (base - 210) * k), (640 * k, (base - 262) * k), (740 * k, (base - 210) * k)])
        R(636, base - 300, 5, 42)
        pygame.draw.polygon(g, (255, 201, 77), [(641 * k, (base - 300) * k), (674 * k, (base - 290) * k), (641 * k, (base - 280) * k)])
        for i in range(8):
            for j in range(2):
                R(404 + i * 62, base - 126 + j * 62, 34, 38, luz if (i + j) % 3 else claro, 4)
        R(610, base - 62, 60, 62, claro, 8)
        for x in (150, 250, 1010, 1120):
            R(x + 16, base - 60, 10, 70)
            pygame.draw.circle(g, col, ((x + 21) * k, (base - 84) * k), 46 * k)
            pygame.draw.circle(g, claro, ((x + 8) * k, (base - 96) * k), 20 * k)
    elif motivo == "patio":
        for x in (90, 1130):
            R(x + 22, base - 80, 12, 90)
            pygame.draw.circle(g, col, ((x + 28) * k, (base - 110) * k), 60 * k)
            pygame.draw.circle(g, claro, ((x + 10) * k, (base - 126) * k), 26 * k)
        R(250, base - 110, 6, 110)
        R(390, base - 110, 6, 110)
        R(244, base - 114, 158, 7)
        for x in (290, 350):
            R(x, base - 108, 2, 62)
            R(x - 12, base - 48, 26, 5)
        R(880, base - 70, 130, 8)
        pygame.draw.polygon(g, col, [(880 * k, (base - 70) * k), (840 * k, base * k), (852 * k, base * k), (892 * k, (base - 62) * k)])
        R(1004, base - 70, 6, 70)
    elif motivo == "mesas":
        for x in (150, 470, 810, 1130):
            pygame.draw.ellipse(g, col, ((x - 90) * k, (base - 40) * k, 180 * k, 44 * k))
            R(x - 6, base - 20, 12, 30)
            for dx in (-66, 66):
                pygame.draw.circle(g, col, ((x + dx) * k, (base - 54) * k), 20 * k)
                R(x + dx - 14, base - 40, 28, 40, col, 8)
        for x in (300, 640, 980):
            R(x - 2, 74, 4, 60)
            pygame.draw.polygon(g, col, [((x - 34) * k, 160 * k), ((x + 34) * k, 160 * k), ((x + 16) * k, 130 * k), ((x - 16) * k, 130 * k)])
            pygame.draw.circle(g, luz, (x * k, 162 * k), 7 * k)
    elif motivo == "casilleros":
        for i in range(22):
            x = 20 + i * 58
            R(x, base - 150, 52, 160, col, 4)
            R(x + 8, base - 136, 36, 8, claro, 3)
            R(x + 40, base - 76, 5, 14, claro, 2)
        for i in range(7):
            R(120 + i * 170, 74, 110, 12, claro, 5)
    elif motivo == "chat":
        for i in range(26):
            x, y = rng.uniform(30, W - 190), rng.uniform(100, H - 150)
            w = rng.uniform(70, 170)
            R(x, y, w, 30, col if i % 2 else claro, 15)
            pygame.draw.polygon(g, col if i % 2 else claro, [((x + 16) * k, (y + 26) * k), ((x + 34) * k, (y + 26) * k), ((x + 12) * k, (y + 42) * k)])
    elif motivo == "cancha":
        for x in (60, W - 60):
            R(x - 5, base - 190, 10, 200)
            R(x - 46, base - 232, 92, 60, col, 6)
            pygame.draw.circle(g, claro, (x * k, (base - 172) * k), 16 * k, int(4 * k))
        for i in range(9):
            R(170 + i * 110, base - 26, 80, 8, claro, 4)
    elif motivo == "reja":
        for i in range(34):
            x = 20 + i * 38
            R(x, base - 120, 7, 130, col, 3)
            pygame.draw.polygon(g, col, [((x - 4) * k, (base - 120) * k), ((x + 3.5) * k, (base - 142) * k), ((x + 11) * k, (base - 120) * k)])
        R(0, base - 96, W, 7)
        R(0, base - 30, W, 7)
        R(930, base - 170, 230, 110, claro, 18)
        for i in range(4):
            R(950 + i * 50, base - 152, 36, 40, luz, 6)
        for x in (980, 1110):
            pygame.draw.circle(g, col, (x * k, (base - 56) * k), 22 * k)
    elif motivo == "noche":
        for _ in range(110):
            x, y = rng.uniform(0, W), rng.uniform(80, H - 220)
            pygame.draw.circle(g, (255, 255, 255, rng.randint(50, 190)), (x * k, y * k), rng.uniform(0.8, 2.2) * k)
        pygame.draw.circle(g, (255, 240, 200), (1080 * k, 170 * k), 46 * k)
        pygame.draw.circle(g, (22, 26, 78), (1062 * k, 158 * k), 40 * k)
        x = 0
        while x < W:
            w, h = rng.uniform(70, 150), rng.uniform(80, 230)
            R(x, base - h + 10, w, h)
            for i in range(int(w // 26)):
                for j in range(int(h // 34)):
                    if rng.random() < 0.4:
                        R(x + 8 + i * 26, base - h + 24 + j * 34, 12, 16, luz, 2)
            x += w + 6
    elif motivo == "libros":
        for bx in (40, 880):
            R(bx, base - 230, 360, 240, col, 6)
            for fila in range(4):
                x = bx + 12
                while x < bx + 340:
                    w, h = rng.uniform(10, 22), rng.uniform(30, 46)
                    R(x, base - 222 + fila * 56 + (48 - h), w, h, rng.choice([claro, aclarar(col, 0.2), (150, 90, 80), (90, 120, 130)]), 2)
                    x += w + 3
        pygame.draw.ellipse(g, col, (480 * k, (base - 44) * k, 320 * k, 50 * k))
        pygame.draw.circle(g, luz, (640 * k, 150 * k), 9 * k)
        pygame.draw.polygon(g, col, [(600 * k, 150 * k), (680 * k, 150 * k), (660 * k, 118 * k), (620 * k, 118 * k)])
        R(638, 74, 4, 46)
    # piso
    R(0, base, W, 96, oscurecer(col, 0.12))


def escenario(lugar, contraste=False, W=1280, H=720):
    """Fondo completo de un lugar: cielo en degradado, siluetas, piso, luz sobre Sam y viñeta."""
    clave = ("escenario", lugar, contraste)
    if clave in _cache:
        return _cache[clave]
    if contraste:
        s = pygame.Surface((W, H))
        s.fill((0, 0, 0))
        pygame.draw.circle(s, (26, 26, 26), (640, 410), 300)
        pygame.draw.circle(s, (0, 0, 0), (640, 410), 296)
        _cache[clave] = s
        return s
    arriba, medio, abajo, sil, piso, motivo = LUGARES.get(lugar, LUGARES["Pasillo"])
    s = degradado(W, H, arriba, abajo, medio)
    rng = random.Random(hash(lugar) % 9973)
    k = 2
    capa = pygame.Surface((W * k, H * k), pygame.SRCALPHA)
    _siluetas(capa, k, motivo, sil, W, H, rng)
    s.blit(pygame.transform.smoothscale(capa, (W, H)), (0, 0))
    # zona de juego: un velo oscuro mantiene legibles las burbujas y una luz cálida marca a Sam
    velo = pygame.Surface((W, H), pygame.SRCALPHA)
    velo.fill((14, 10, 34, 105 if motivo != "vacio" else 60))
    s.blit(velo, (0, 0))
    for r, a in ((330, 26), (250, 30), (170, 34)):
        pygame.draw.circle(s, mezclar(piso, (255, 230, 170), 0.1), (640, 410), r, 2)
    s.blit(halo(380, (255, 214, 150), 70, 1.6), (640 - 380, 410 - 380))
    s.blit(vineta(W, H, 170), (0, 0))
    _cache[clave] = s
    return s


def limpiar():
    _cache.clear()


# ------------------------------------------------------------------ efectos (los usa juego.py en una línea)
def capa(color, alfa, W=1280, H=720):
    """Velo de un color sobre toda la pantalla (frío cuando Sam está mal, destello de la onda, golpe)."""
    clave = ("capa", color)
    if clave not in _cache:
        s = pygame.Surface((W, H))
        s.fill(color)
        _cache[clave] = s
    s = _cache[clave]
    s.set_alpha(max(0, min(255, int(alfa))))
    return s


def tenido(sprite, color, fuerza):
    """Copia del sprite pintada de un color (Sam se pone rojo cuando lo golpean)."""
    s = sprite.copy()
    s.fill((*color, 0), special_flags=pygame.BLEND_RGBA_MAX)
    s.fill((255, 255, 255, int(255 * fuerza)), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def desenfocado(superficie, oscuridad=170):
    """Fondo borroso y oscuro para las ventanas de pausa, ayuda y récords."""
    w, h = superficie.get_size()
    s = pygame.transform.smoothscale(pygame.transform.smoothscale(superficie, (w // 10, h // 10)), (w, h))
    s.blit(capa((16, 10, 40), oscuridad, w, h), (0, 0))
    return s


def onda_voz(dest, centro, radio, color=(255, 197, 61)):
    """Dibujo de '¡Alza la voz!': destello, aro dorado con rayos y una onda que cruza la pantalla."""
    k = min(1.0, radio / 520)
    if radio < 150:
        dest.blit(capa((255, 250, 230), 200 * (1 - radio / 150)), (0, 0))
    pygame.draw.circle(dest, (255, 236, 170), centro, int(radio * 2.6), max(2, int(10 * (1 - k))))
    pygame.draw.circle(dest, color, centro, int(radio), max(4, int(16 * (1 - k))))
    if radio > 40:
        pygame.draw.circle(dest, (255, 255, 255), centro, int(radio) - 18, max(2, int(6 * (1 - k))))
    for i in range(12):
        a = i * math.pi / 6 + radio / 200
        p1 = (centro[0] + math.cos(a) * (radio + 6), centro[1] + math.sin(a) * (radio + 6))
        p2 = (centro[0] + math.cos(a) * (radio + 28), centro[1] + math.sin(a) * (radio + 28))
        pygame.draw.line(dest, color, p1, p2, 4)


def confeti(dest, t, n=40, W=1280, H=720):
    """Papelitos de colores que caen (victoria). t = segundos desde que empezó."""
    colores = [(255, 197, 61), (46, 229, 157), (167, 139, 250), (56, 214, 255), (255, 107, 90)]
    for i in range(n):
        x = (i * 97 + t * 60) % W
        y = (i * 53 + t * (120 + (i % 5) * 20)) % H
        pygame.draw.rect(dest, colores[i % 5], (x, y, 8, 12), border_radius=2)


def cara(tam, camiseta, pelo, piel, estilo, expresion, apagado=False):
    """Solo la cabeza de un personaje (para el HUD)."""
    spr = nino(tam * 2, camiseta, pelo, piel, estilo, expresion, apagado)
    return spr.subsurface((0, 0, spr.get_width(), int(spr.get_height() * 0.6)))
