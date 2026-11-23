"""Mide el balance con el jugador quieto (20 semillas) y el tiempo por cuadro con 40 mensajes y 150 chispas.

  python pruebas/balance_y_rendimiento.py
"""
import os
import random
import statistics
import sys
import tempfile
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import pygame  # noqa: E402

import juego as J  # noqa: E402

J.RUTA_RECORDS = os.path.join(tempfile.mkdtemp(), "records.csv")
pygame.mouse.get_pressed = lambda *a, **k: (False, False, False)   # nadie toca el ratón


def quieto(j, semilla, aliados):
    random.seed(semilla)
    j.nueva_partida()
    if aliados:
        j.sumar_valentia(80)                      # los 8 testigos ayudan desde el inicio
    for _ in range(60 * 60 * 15):
        if j.pantallas.ver_tope() != "juego":
            break
        j.actualizar(1 / 60)
    return j.oleada, j.resultado, j.stats["frenados"], j.stats["apoyos"]


def balance(j):
    for aliados in (True, False):
        r = [quieto(j, s, aliados) for s in range(20)]
        ol = sorted(x[0] for x in r)
        print(f"Quieto {'con 8 aliados' if aliados else 'sin ayuda   '}: oleada mediana {statistics.median(ol):g} "
              f"(rango {ol[0]}-{ol[-1]}), victorias {sum(x[1] == 'victoria' for x in r)}/20, "
              f"frenados mediana {statistics.median(x[2] for x in r):g}, "
              f"apoyos mediana {statistics.median(x[3] for x in r):g}")


def rendimiento(j):
    random.seed(1)
    j.nueva_partida()
    j.oleada = 7
    j.siguiente_oleada()
    tiempos = []
    for i in range(1800):
        while j.mensajes.tam < 40:                 # siempre 40 mensajes en pantalla
            j.crear_mensaje(random.random() < 0.3, random.uniform(0, 6.28), 40)
        while j.chispas.tam < 150:
            j.chispas.agregar({"pos": pygame.Vector2(640, 360), "vida": 0.5,
                               "vel": pygame.Vector2(random.uniform(-200, 200), random.uniform(-200, 200))})
        j.animo = 100
        a = time.perf_counter()
        j.actualizar(1 / 60)
        j.dibujar()
        tiempos.append((time.perf_counter() - a) * 1000)
    tiempos.sort()
    print(f"40 mensajes y 150 chispas, actualizar + dibujar: mediana {statistics.median(tiempos):.2f} ms, "
          f"p95 {tiempos[int(len(tiempos) * 0.95)]:.2f} ms (límite a 60 FPS: 16,7 ms)")


if __name__ == "__main__":
    j = J.Juego()
    balance(j)
    rendimiento(j)
