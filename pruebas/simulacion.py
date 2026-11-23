"""Un bot juega partidas completas sin abrir ventana y se cuentan los errores.

  python pruebas/simulacion.py
"""
import os
import random
import sys
import tempfile
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import pygame  # noqa: E402

import juego as J  # noqa: E402
from juego import Corazon  # noqa: E402

J.RUTA_RECORDS = os.path.join(tempfile.mkdtemp(), "records.csv")  # no tocar los récords reales


def tecla(j, k):
    j.evento(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=""))


def jugar(j, inmortal, caos=False, segundos=900):
    j.nueva_partida()
    tiempos = []
    for i in range(int(segundos * 60)):
        if j.pantallas.ver_tope() == "final":
            break
        if j.pantallas.ver_tope() != "juego":
            tecla(j, pygame.K_ESCAPE)
            continue
        if inmortal:
            j.animo = max(j.animo, 50)
        acosos = [m for m in j.mensajes if not m.apoyo]
        if acosos and i % 10 == 0:  # el bot dispara al acoso más cercano a Sam
            objetivo = min(acosos, key=lambda m: m.pos.distance_to(J.SAM)).pos
            j.corazones.agregar(Corazon(j.jugador, (objetivo - j.jugador).normalize()))
        if j.jefe and i % 8 == 0:
            j.corazones.agregar(Corazon(j.jugador, (j.jefe["pos"] - j.jugador).normalize()))
        if j.impulso >= 100:
            j.alza_la_voz()
        if caos and random.random() < 0.05:
            tecla(j, random.choice([pygame.K_q, pygame.K_9, pygame.K_F2, pygame.K_h, pygame.K_p, pygame.K_F1]))
        a = time.perf_counter()
        j.actualizar(1 / 60)
        if i % 3 == 0:
            j.dibujar()
        tiempos.append(time.perf_counter() - a)
    tiempos.sort()
    return tiempos[len(tiempos) // 2] * 1000 if tiempos else 0


def main():
    random.seed(3)
    errores = 0
    j = J.Juego()
    for nombre, inmortal, caos in (("A (Sam no cae)", True, False), ("B (normal)", False, False),
                                   ("C (teclas al azar)", True, True)):
        try:
            ms = jugar(j, inmortal, caos)
            print(f"Partida {nombre}: {j.resultado or 'sin terminar'} · oleada {j.oleada} · puntos {j.puntos} · "
                  f"frenados {j.stats['frenados']} · apoyos {j.stats['apoyos']} · "
                  f"testigos {sum(1 for t in j.testigos if t.aliado)} · {ms:.1f} ms por cuadro")
        except Exception as ex:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            errores += 1
            print(f"Partida {nombre}: ERROR {ex!r}")
    # nombre con caracteres raros y guardado del récord
    j.evento(pygame.event.Event(pygame.TEXTINPUT, text="Bot<>;'😀ñ 1234567890xyz"))
    tecla(j, pygame.K_ESCAPE)
    print("Nombre guardado:", j.records[:1], "· pantalla:", j.pantallas.ver_tope())
    # archivos dañados: el juego debe arrancar igual
    with open(J.RUTA_RECORDS, "wb") as f:
        f.write(b"\xff\xfe basura,,\nAna,abc\n")
    original = J.RUTA_TEXTOS
    J.RUTA_TEXTOS = os.path.join(tempfile.mkdtemp(), "no_existe.json")
    try:
        j2 = J.Juego()
        jugar(j2, True, segundos=5)
        print("Archivos dañados: el juego arrancó y jugó sin errores")
    except Exception as ex:  # noqa: BLE001
        errores += 1
        print("Archivos dañados: ERROR", ex)
    J.RUTA_TEXTOS = original
    print("errores:", errores)


if __name__ == "__main__":
    main()
