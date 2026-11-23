"""Lanzador del .exe: el juego lee las frases empaquetadas y guarda los récords junto al .exe."""
import os
import sys

import pygame

import juego

juego.RUTA_RECORDS = os.path.join(os.path.dirname(sys.executable), "records.csv")
try:
    juego.Juego().correr()
except SystemExit:
    pygame.quit()
