"""Prueba de usabilidad con bots: cinco perfiles de jugador manejan el juego SOLO con teclado y ratón
simulados (pasan por Juego.evento y por pygame.key/mouse), como lo haría una persona.
No reemplaza la prueba con usuarios reales: sirve para encontrar fallos antes de hacerla.

  python pruebas/usabilidad_bots.py
"""
import os
import random
import sys
import tempfile
import time
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import pygame  # noqa: E402

import juego as J  # noqa: E402

J.RUTA_RECORDS = os.path.join(tempfile.mkdtemp(), "records.csv")

# ---------------------------------------------------------------- entrada simulada
ENTRADA = {"teclas": set(), "clic": False, "raton": (640, 360)}


class Teclas:
    def __getitem__(self, k):
        return k in ENTRADA["teclas"]


pygame.key.get_pressed = lambda: Teclas()
pygame.mouse.get_pressed = lambda *a, **k: (ENTRADA["clic"], False, False)
pygame.mouse.get_pos = lambda: ENTRADA["raton"]


def tecla(j, k, texto=""):
    j.evento(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=texto))


def escribir(j, texto):
    j.evento(pygame.event.Event(pygame.TEXTINPUT, text=texto))


def clic_boton(j, i):
    j.dibujar()  # los botones se calculan al dibujar el menú
    r = j.botones[i]
    j.evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=r.center, button=1))


# ---------------------------------------------------------------- invariantes
def revisar(j, fallos, perfil):
    def f(msg):
        if msg not in fallos[perfil]:
            fallos[perfil].append(msg)
    if not 0 <= j.impulso <= 100:
        f(f"impulso fuera de rango: {j.impulso}")
    if j.animo > 100:
        f(f"ánimo > 100: {j.animo}")
    if j.puntos < 0:
        f(f"puntos negativos: {j.puntos}")
    for nombre in ("mensajes", "corazones", "chispas", "textos"):
        lista = getattr(j, nombre)
        n = sum(1 for _ in lista)
        if n != lista.tam:
            f(f"{nombre}: tam={lista.tam} pero hay {n} nodos")
    if j.corazones.tam > 400:
        f(f"corazones acumulados: {j.corazones.tam}")
    if j.chispas.tam > 1500:
        f(f"chispas acumuladas: {j.chispas.tam}")
    if j.pantallas.tam > 4:
        f(f"pila de pantallas creció a {j.pantallas.tam}")
    lejos = [m for m in j.mensajes if not (-400 < m.pos.x < J.ANCHO + 400 and -400 < m.pos.y < J.ALTO + 400)]
    if lejos:
        f(f"{len(lejos)} mensajes fuera de pantalla sin borrar")
    if not (0 <= j.jugador.x <= J.ANCHO and 0 <= j.jugador.y <= J.ALTO):
        f(f"jugador fuera de pantalla: {j.jugador}")


# ---------------------------------------------------------------- perfiles
def mas_cercano(j, apoyo=None):
    ms = [m for m in j.mensajes if apoyo is None or m.apoyo == apoyo]
    return min(ms, key=lambda m: m.pos.distance_to(J.SAM)) if ms else None


def experto(j, i):
    m = mas_cercano(j, apoyo=False)
    if j.jefe and (not m or m.pos.distance_to(J.SAM) > 220):
        ENTRADA["raton"], ENTRADA["clic"] = tuple(j.jefe["pos"]), True
    elif m:
        ENTRADA["raton"], ENTRADA["clic"] = (int(m.pos.x), int(m.pos.y)), True
    else:
        ENTRADA["clic"] = False
    if j.impulso >= 100:
        tecla(j, pygame.K_SPACE)


def novato(j, i):
    # dispara con retraso y apunta mal: a veces al mensaje más cercano sin mirar si es apoyo
    if i % 30 == 0:
        m = mas_cercano(j)
        if m:
            ENTRADA["raton"] = (int(m.pos.x + random.uniform(-40, 40)), int(m.pos.y + random.uniform(-40, 40)))
        ENTRADA["clic"] = random.random() < 0.7
    if i % 240 == 0:
        ENTRADA["teclas"] = {random.choice([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d])}
    if i == 600:
        tecla(j, pygame.K_h)       # busca la ayuda
    if i == 700:
        tecla(j, pygame.K_ESCAPE)  # y vuelve


def gatillo_facil(j, i):
    # dispara a TODO lo que se acerca (también a los apoyos): mide si entiende el castigo
    m = mas_cercano(j)
    ENTRADA["clic"] = m is not None
    if m:
        ENTRADA["raton"] = (int(m.pos.x), int(m.pos.y))
    if j.impulso >= 100 and i % 50 == 0:
        tecla(j, pygame.K_SPACE)


def caos(j, i):
    # aporrea teclas, abre y cierra pausa, recorre el buzón, cambia contraste y panel, mueve el ratón
    if random.random() < 0.08:
        tecla(j, random.choice([pygame.K_q, pygame.K_9, pygame.K_F1, pygame.K_F2, pygame.K_h, pygame.K_p,
                                pygame.K_ESCAPE, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN,
                                pygame.K_BACKSPACE, pygame.K_SPACE, pygame.K_TAB, pygame.K_z]))
    ENTRADA["teclas"] = set(random.sample([pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_UP,
                                           pygame.K_LEFT], k=random.randint(0, 3)))
    ENTRADA["raton"] = (random.randint(-50, J.ANCHO + 50), random.randint(-50, J.ALTO + 50))
    ENTRADA["clic"] = random.random() < 0.5
    if j.pantallas.ver_tope() == "pausa" and random.random() < 0.02:
        tecla(j, pygame.K_p)  # que no se quede para siempre en pausa


def quieto(j, i):
    ENTRADA["clic"] = False
    ENTRADA["teclas"] = set()


PERFILES = [("Experto", experto), ("Novato", novato), ("Gatillo fácil", gatillo_facil),
            ("Teclas al azar", caos), ("Se queda quieto", quieto)]


# ---------------------------------------------------------------- una sesión = como en correr()
def sesion(j, perfil, accion, fallos, maximo=60 * 60 * 12):
    datos = {"t_primer_frenado": None, "disparos_apoyo": 0, "errores": 0, "cuadros": 0, "tiempos": []}
    original = j.disparo_a_apoyo

    def contar(m):
        datos["disparos_apoyo"] += 1
        original(m)
    j.disparo_a_apoyo = contar

    # entra al juego con el ratón, como una persona: clic en el primer botón del menú
    clic_boton(j, 0)
    if j.pantallas.ver_tope() != "juego":
        fallos[perfil].append("el clic en 'Jugar' no abrió la partida")
        return datos
    t0 = 0.0
    for i in range(maximo):
        if j.pantallas.ver_tope() == "final":
            break
        try:
            accion(j, i)
            pantalla = j.pantallas.ver_tope()
            a = time.perf_counter()
            if pantalla == "juego":
                j.actualizar(1 / 60)
                t0 += 1 / 60
            if i % 4 == 0:
                j.dibujar()
            datos["tiempos"].append(time.perf_counter() - a)
            if datos["t_primer_frenado"] is None and j.stats["frenados"]:
                datos["t_primer_frenado"] = t0
            if pantalla == "menu":   # el caos salió con Q: vuelve a jugar
                clic_boton(j, 0)
            revisar(j, fallos, perfil)
        except SystemExit:
            fallos[perfil].append("el juego se cerró (SystemExit) durante la partida")
            break
        except Exception:
            datos["errores"] += 1
            if datos["errores"] <= 2:
                fallos[perfil].append("EXCEPCIÓN: " + traceback.format_exc().strip().splitlines()[-1])
            j.ir_al_menu()
        datos["cuadros"] = i
    datos["oleada"], datos["resultado"] = j.oleada, j.resultado or "sin terminar"
    datos["frenados"], datos["apoyos"] = j.stats["frenados"], j.stats["apoyos"]
    datos["aliados"] = sum(1 for t in j.testigos if t.aliado)
    datos["buzon"] = j.buzon.tam
    datos["puntos"] = j.puntos
    j.disparo_a_apoyo = original
    return datos


def pantalla_final(j, fallos, perfil):
    """Escribe un nombre difícil, borra, guarda, y revisa los récords."""
    if j.pantallas.ver_tope() != "final":
        return
    try:
        escribir(j, "Ñandú 😀 <script> 1234567890")
        for _ in range(3):
            tecla(j, pygame.K_BACKSPACE)
        j.dibujar()
        nombre = j.nombre
        if len(nombre) > 12:
            fallos[perfil].append(f"nombre de {len(nombre)} caracteres")
        tecla(j, pygame.K_ESCAPE)
        if j.pantallas.ver_tope() != "menu":
            fallos[perfil].append("ESC en la pantalla final no volvió al menú")
        if not any(n == (nombre.strip() or "Jugador") for n, _p in j.records):
            fallos[perfil].append(f"el récord '{nombre}' no aparece en records")
        if len(j.records) > 5:
            fallos[perfil].append(f"records guarda {len(j.records)} (> 5)")
        j.pantallas.apilar("records")
        j.dibujar()
        tecla(j, pygame.K_ESCAPE)
    except Exception:
        fallos[perfil].append("EXCEPCIÓN en pantalla final: " + traceback.format_exc().strip().splitlines()[-1])


def menu_y_pausa(j, fallos):
    """Recorre el menú con teclado y la pausa con el buzón vacío y lleno."""
    p = "Menú y pausa"
    fallos[p] = []
    try:
        j.ir_al_menu()
        for k in (pygame.K_DOWN,) * 5 + (pygame.K_UP,) * 7:
            tecla(j, k)
        j.dibujar()
        j.menu_sel = 0
        for nombre_op, accion in j.opciones_menu():
            if accion in ("ayuda", "records"):
                j.accion_menu(accion)
                j.dibujar()
                tecla(j, pygame.K_ESCAPE)
                if j.pantallas.ver_tope() != "menu":
                    fallos[p].append(f"ESC en '{accion}' no volvió al menú")
        tecla(j, pygame.K_RETURN)                   # Jugar con Enter
        tecla(j, pygame.K_p)
        for k in (pygame.K_LEFT, pygame.K_RIGHT) * 3:   # buzón vacío
            tecla(j, k)
        j.dibujar()
        tecla(j, pygame.K_p)
        for _ in range(5):
            j.buzon.agregar_final("frase de prueba muy larga " * 6)
        tecla(j, pygame.K_ESCAPE)
        for k in (pygame.K_LEFT,) * 9 + (pygame.K_RIGHT,) * 12:
            tecla(j, k)
            j.dibujar()
        tecla(j, pygame.K_q)
        if j.pantallas.ver_tope() != "menu":
            fallos[p].append("Q en pausa no volvió al menú")
        for _ in range(20):                           # contraste y panel muchas veces
            tecla(j, pygame.K_F1)
            tecla(j, pygame.K_F2)
            j.dibujar()
    except Exception:
        fallos[p].append("EXCEPCIÓN: " + traceback.format_exc().strip().splitlines()[-1])


def main():
    random.seed(11)
    j = J.Juego()
    fallos, resumen = {}, []
    for perfil, accion in PERFILES:
        fallos[perfil] = []
        ENTRADA.update(teclas=set(), clic=False, raton=(640, 360))
        j.ir_al_menu()
        d = sesion(j, perfil, accion, fallos)
        pantalla_final(j, fallos, perfil)
        t = sorted(d["tiempos"]) or [0]
        resumen.append((perfil, d, t[len(t) // 2] * 1000, t[int(len(t) * 0.99)] * 1000))
    menu_y_pausa(j, fallos)

    print(f"{'Perfil':16} {'Resultado':10} {'Ol.':>3} {'1er frenado':>11} {'Frenados':>8} {'Apoyos':>6} "
          f"{'Disp.apoyo':>10} {'Aliados':>7} {'Buzón':>5} {'Puntos':>6} {'ms med':>6} {'ms p99':>6} {'Err':>3}")
    for perfil, d, med, p99 in resumen:
        primero = f"{d['t_primer_frenado']:.1f} s" if d["t_primer_frenado"] is not None else "nunca"
        print(f"{perfil:16} {d['resultado']:10} {d['oleada']:>3} {primero:>11} {d['frenados']:>8} {d['apoyos']:>6} "
              f"{d['disparos_apoyo']:>10} {d['aliados']:>7} {d['buzon']:>5} {d['puntos']:>6} {med:>6.2f} "
              f"{p99:>6.2f} {d['errores']:>3}")
    print("\nFALLOS ENCONTRADOS")
    total = 0
    for perfil, lista in fallos.items():
        for f in lista:
            total += 1
            print(f"  [{perfil}] {f}")
    print(f"  total: {total}")


if __name__ == "__main__":
    main()
