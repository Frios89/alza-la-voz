"""Estructuras de datos de Alza la Voz, hechas a mano con nodos.

No se usan las listas de Python como pila o cola ni la clase deque: cada operación
se puede seguir nodo por nodo.
"""
import random


class Nodo:
    """Un dato y una flecha al siguiente nodo."""

    def __init__(self, dato):
        self.dato = dato
        self.sig = None


class NodoDoble:
    """Un dato y dos flechas: al siguiente y al anterior."""

    def __init__(self, dato):
        self.dato = dato
        self.sig = None
        self.ant = None


# ---------------------------------------------------------------- COLA (FIFO)
class Cola:
    """Uso en el juego: los mensajes programados de la oleada, en orden de llegada."""

    def __init__(self):
        self.frente = None   # de aquí se saca
        self.fin = None      # aquí se agrega
        self.tam = 0

    def encolar(self, dato):
        nuevo = Nodo(dato)
        if self.fin is None:          # cola vacía: el nuevo es frente y fin
            self.frente = nuevo
        else:
            self.fin.sig = nuevo      # el último apunta al nuevo
        self.fin = nuevo
        self.tam += 1

    def desencolar(self):
        if self.frente is None:
            return None
        dato = self.frente.dato
        self.frente = self.frente.sig
        if self.frente is None:       # se vació: también se limpia el fin
            self.fin = None
        self.tam -= 1
        return dato

    def ver_frente(self):
        return None if self.frente is None else self.frente.dato

    def vacia(self):
        return self.frente is None


# ---------------------------------------------------------------- PILA (LIFO)
class Pila:
    """Uso en el juego: las pantallas abiertas (menú, juego, pausa, ayuda...)."""

    def __init__(self):
        self.tope = None
        self.tam = 0

    def apilar(self, dato):
        nuevo = Nodo(dato)
        nuevo.sig = self.tope         # el nuevo apunta al que estaba arriba
        self.tope = nuevo
        self.tam += 1

    def desapilar(self):
        if self.tope is None:
            return None
        dato = self.tope.dato
        self.tope = self.tope.sig
        self.tam -= 1
        return dato

    def ver_tope(self):
        return None if self.tope is None else self.tope.dato

    def vaciar(self):
        self.tope = None
        self.tam = 0


# ---------------------------------------------------------------- LISTA ENLAZADA
class ListaEnlazada:
    """Uso en el juego: mensajes y corazones en pantalla. Se borran desde cualquier posición."""

    def __init__(self):
        self.cabeza = None
        self.tam = 0

    def agregar(self, dato):
        """Inserta al inicio: O(1), no hay que recorrer."""
        nuevo = Nodo(dato)
        nuevo.sig = self.cabeza
        self.cabeza = nuevo
        self.tam += 1

    def eliminar_si(self, condicion):
        """Quita todos los nodos que cumplan la condición en un solo recorrido: O(n)."""
        anterior, actual = None, self.cabeza
        while actual:
            if condicion(actual.dato):
                if anterior:
                    anterior.sig = actual.sig   # el anterior "salta" sobre el borrado
                else:
                    self.cabeza = actual.sig    # se borró la cabeza
                self.tam -= 1
            else:
                anterior = actual               # solo avanza si no se borró
            actual = actual.sig

    def __iter__(self):
        actual = self.cabeza
        while actual:
            yield actual.dato
            actual = actual.sig


# ---------------------------------------------------------------- LISTA CIRCULAR
class ListaCircular:
    """Uso en el juego: los 8 testigos alrededor de Sam. El valor se contagia al vecino."""

    def __init__(self):
        self.actual = None   # nodo donde está el "cursor"
        self.tam = 0

    def agregar(self, dato):
        nuevo = Nodo(dato)
        if self.actual is None:
            nuevo.sig = nuevo         # un solo nodo: se apunta a sí mismo
            self.actual = nuevo
        else:                         # se inserta después del actual y el cursor avanza
            nuevo.sig = self.actual.sig
            self.actual.sig = nuevo
            self.actual = nuevo
        self.tam += 1

    def siguiente_que_cumpla(self, condicion):
        """Avanza por el círculo hasta encontrar un dato que cumpla la condición (máx. una vuelta)."""
        nodo = self.actual
        for _ in range(self.tam):
            nodo = nodo.sig
            if condicion(nodo.dato):
                self.actual = nodo
                return nodo.dato
        return None

    def __iter__(self):
        if self.actual is None:
            return
        nodo = self.actual.sig
        for _ in range(self.tam):     # una vuelta completa, empezando después del cursor
            yield nodo.dato
            nodo = nodo.sig


# ---------------------------------------------------------------- LISTA DOBLE
class ListaDoble:
    """Uso en el juego: el buzón de Sam. Se recorre con ← y → en la pausa."""

    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.cursor = None
        self.tam = 0

    def agregar_final(self, dato):
        nuevo = NodoDoble(dato)
        if self.cola is None:
            self.cabeza = self.cola = nuevo
        else:
            nuevo.ant = self.cola     # el nuevo mira hacia atrás al último
            self.cola.sig = nuevo     # el último mira hacia adelante al nuevo
            self.cola = nuevo
        self.cursor = nuevo           # el cursor queda en lo más reciente
        self.tam += 1

    def anterior(self):
        if self.cursor and self.cursor.ant:
            self.cursor = self.cursor.ant

    def siguiente(self):
        if self.cursor and self.cursor.sig:
            self.cursor = self.cursor.sig

    def valor_cursor(self):
        return None if self.cursor is None else self.cursor.dato

    def posicion_cursor(self):
        """Número del nodo del cursor contando desde la cabeza (1, 2, ...)."""
        pos, nodo = 0, self.cabeza
        while nodo:
            pos += 1
            if nodo is self.cursor:
                return pos
            nodo = nodo.sig
        return 0


# ---------------------------------------------------------------- MULTILISTA
class Multilista:
    """Uso en el juego: el banco de frases. Lista de categorías, y cada categoría tiene su lista de frases."""

    def __init__(self):
        self.cabeza = None   # primera categoría

    def _buscar(self, categoria):
        nodo = self.cabeza
        while nodo:
            if nodo.dato["nombre"] == categoria:
                return nodo
            nodo = nodo.sig
        return None

    def agregar_frase(self, categoria, frase):
        nodo_cat = self._buscar(categoria)
        if nodo_cat is None:          # categoría nueva: se agrega a la lista principal
            nodo_cat = Nodo({"nombre": categoria, "frases": ListaEnlazada()})
            nodo_cat.sig = self.cabeza
            self.cabeza = nodo_cat
        nodo_cat.dato["frases"].agregar(frase)   # la frase va a la sublista de su categoría

    def frase_al_azar(self, categoria):
        nodo_cat = self._buscar(categoria)
        if nodo_cat is None or nodo_cat.dato["frases"].tam == 0:
            return "..."
        k = random.randrange(nodo_cat.dato["frases"].tam)
        for i, frase in enumerate(nodo_cat.dato["frases"]):
            if i == k:
                return frase

    def categorias(self):
        nodo = self.cabeza
        while nodo:
            yield nodo.dato["nombre"], nodo.dato["frases"].tam
            nodo = nodo.sig
