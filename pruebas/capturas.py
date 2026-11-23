"""Guarda una captura de cada pantalla en pruebas/capturas/ (para el informe y el pendón)."""
import os
import random
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import juego as J  # noqa: E402
from juego import Corazon  # noqa: E402

J.RUTA_RECORDS = os.path.join(tempfile.mkdtemp(), "records.csv")
DESTINO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "capturas")
os.makedirs(DESTINO, exist_ok=True)


def foto(j, nombre):
    j.dibujar()
    pygame.image.save(j.pantalla, os.path.join(DESTINO, nombre + ".png"))


def jugar(j, segundos):
    for i in range(int(segundos * 60)):
        if j.pantallas.ver_tope() != "juego":
            return
        j.animo = max(j.animo, 60)
        acosos = [m for m in j.mensajes if not m.apoyo]
        if acosos and i % 14 == 0:
            objetivo = min(acosos, key=lambda m: m.pos.distance_to(J.SAM)).pos
            j.corazones.agregar(Corazon(j.jugador, (objetivo - j.jugador).normalize()))
        j.actualizar(1 / 60)


random.seed(5)
j = J.Juego()
foto(j, "01_menu")
j.pantallas.apilar("ayuda")
foto(j, "02_como_jugar")
j.pantallas.desapilar()
for oleada in (1, 3, 5, 7, 9, 10):
    j.nueva_partida()
    j.oleada = oleada - 1
    j.valentia = 5 * oleada
    j.sumar_valentia(0)
    j.siguiente_oleada()
    jugar(j, 9)
    foto(j, f"03_oleada{oleada:02d}")
j.impulso = 100
j.alza_la_voz()
for _ in range(10):
    j.actualizar(1 / 60)
foto(j, "04_alza_la_voz")
j.panel_estructuras = True
foto(j, "05_panel_estructuras")
j.panel_estructuras = False
j.contraste = True
j.cache.clear()
foto(j, "06_alto_contraste")
j.contraste = False
j.cache.clear()
j.pantallas.apilar("pausa")
foto(j, "07_pausa_buzon")
j.pantallas.desapilar()
j.terminar(True)
foto(j, "08_victoria")
j.resultado = "derrota"
foto(j, "09_derrota")
print("capturas en", DESTINO)
