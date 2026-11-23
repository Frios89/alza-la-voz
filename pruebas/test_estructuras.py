"""Pruebas de cada estructura de datos.  python pruebas/test_estructuras.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from estructuras import Cola, ListaCircular, ListaDoble, ListaEnlazada, Multilista, Pila  # noqa: E402


def test_cola_fifo():
    c = Cola()
    for x in (1, 2, 3):
        c.encolar(x)
    assert [c.desencolar(), c.desencolar(), c.desencolar(), c.desencolar()] == [1, 2, 3, None]
    assert c.vacia() and c.fin is None


def test_pila_lifo():
    p = Pila()
    for x in ("menu", "juego", "pausa"):
        p.apilar(x)
    assert p.ver_tope() == "pausa" and p.desapilar() == "pausa" and p.ver_tope() == "juego" and p.tam == 2


def test_lista_enlazada_borra_inicio_medio_y_final():
    lista = ListaEnlazada()
    for x in range(6):
        lista.agregar(x)              # queda 5,4,3,2,1,0
    lista.eliminar_si(lambda x: x in (5, 2, 0))
    assert list(lista) == [4, 3, 1] and lista.tam == 3


def test_lista_circular_da_la_vuelta():
    c = ListaCircular()
    for x in range(4):
        c.agregar({"id": x, "aliado": False})
    vistos = []
    for _ in range(4):
        t = c.siguiente_que_cumpla(lambda d: not d["aliado"])
        t["aliado"] = True
        vistos.append(t["id"])
    assert sorted(vistos) == [0, 1, 2, 3]
    assert c.siguiente_que_cumpla(lambda d: not d["aliado"]) is None   # una vuelta completa sin éxito


def test_lista_doble_cursor():
    d = ListaDoble()
    for x in "abc":
        d.agregar_final(x)
    assert d.valor_cursor() == "c"
    d.anterior()
    d.anterior()
    d.anterior()                       # no pasa de la cabeza
    assert d.valor_cursor() == "a" and d.posicion_cursor() == 1
    d.siguiente()
    assert d.valor_cursor() == "b"


def test_multilista():
    m = Multilista()
    m.agregar_frase("malos:burla", "Jaja")
    m.agregar_frase("malos:burla", "Qué raro")
    m.agregar_frase("buenos:apoyo", "No estás solo")
    assert dict(m.categorias()) == {"buenos:apoyo": 1, "malos:burla": 2}
    assert m.frase_al_azar("malos:burla") in ("Jaja", "Qué raro")
    assert m.frase_al_azar("no existe") == "..."


if __name__ == "__main__":
    for nombre, fn in list(globals().items()):
        if nombre.startswith("test_"):
            fn()
            print("ok", nombre)
