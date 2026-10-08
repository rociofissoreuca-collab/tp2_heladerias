"""Menú de la aplicación: el usuario elige opciones con input() y la app no se rompe con entradas inválidas."""
import os

import pandas as pd

from datos import PATRON_CARPETA, cumple_patron
from heladeria import Heladeria
from recomendador import Recomendador

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 10)


class App:
    """Muestra el menú en un bucle hasta que el usuario elige salir."""

    def __init__(self, carpeta_datos="datos", entrada=input):
        self.carpeta_datos = carpeta_datos
        self.entrada = entrada
        self.heladeria = None
        self.opciones = {
            "1": ("Cargar una heladería", self.cargar, False),
            "2": ("Resumen de ventas por mes", self.ver_resumen, True),
            "3": ("Estacionalidad", self.ver_estacionalidad, True),
            "4": ("Ranking de sabores", self.ver_ranking, True),
            "5": ("Clientes y perfil de consumo", self.ver_clientes, True),
            "6": ("Ventas por canal", self.ver_canales, True),
            "7": ("Inventario: qué reponer y qué se puede vencer", self.ver_inventario, True),
            "8": ("Merma y sabores candidatos a salir", self.ver_merma, True),
            "9": ("Recomendación del próximo sabor", self.ver_recomendacion, True),
        }

    def heladerias_disponibles(self):
        """Carpetas dentro de datos/ con nombre válido (heladeria_...)."""
        if not os.path.isdir(self.carpeta_datos):
            return []
        nombres = sorted(os.listdir(self.carpeta_datos))
        return [n for n in nombres if cumple_patron(PATRON_CARPETA, n)
                and os.path.isdir(os.path.join(self.carpeta_datos, n))]

    def mostrar_menu(self):
        actual = self.heladeria.nombre if self.heladeria else "ninguna"
        print("\n" + "=" * 50)
        print(f"  ANALIZADOR DE HELADERÍAS   (cargada: {actual})")
        print("=" * 50)
        for clave, (texto, _, _) in self.opciones.items():
            print(f"  {clave}. {texto}")
        print("  0. Salir")

    def ejecutar(self):
        while True:
            self.mostrar_menu()
            opcion = self.entrada("Elegí una opción: ").strip()
            if opcion == "0":
                print("¡Hasta luego!")
                break
            self.atender(opcion)
            self.entrada("\n(Apretá Enter para volver al menú) ")

    def atender(self, opcion):
        """Ejecuta la opción elegida; si algo sale mal, muestra el motivo en vez de cortar el programa."""
        if opcion not in self.opciones:
            print("⚠ Opción inválida: escribí un número del menú.")
            return
        texto, accion, necesita_carga = self.opciones[opcion]
        if necesita_carga and self.heladeria is None:
            print("⚠ Primero cargá una heladería (opción 1).")
            return
        try:
            accion()
        except (ValueError, FileNotFoundError, KeyError) as error:
            print(f"⚠ {error}")

    def cargar(self):
        disponibles = self.heladerias_disponibles()
        if not disponibles:
            raise FileNotFoundError(f"No hay heladerías en la carpeta '{self.carpeta_datos}'")
        for numero, nombre in enumerate(disponibles, start=1):
            print(f"  {numero}. {nombre}")
        eleccion = self.entrada("Número de la heladería: ").strip()
        if not eleccion.isdigit() or not 1 <= int(eleccion) <= len(disponibles):
            raise ValueError(f"Elegí un número entre 1 y {len(disponibles)}")
        carpeta = os.path.join(self.carpeta_datos, disponibles[int(eleccion) - 1])
        print("Cargando y limpiando datos...")
        self.heladeria = Heladeria(carpeta)
        print(f"✔ {self.heladeria}")
        descartes = sum(sum(motivos.values()) for motivos in self.heladeria.reporte["descartes"].values())
        print(f"  Se descartaron {descartes} filas con errores de carga.")

    def ver_resumen(self):
        print(self.heladeria.resumen_mensual().to_string())

    def ver_estacionalidad(self):
        tabla = self.heladeria.estacionalidad()
        print(tabla.to_string())
        print(f"Mes más fuerte: {tabla['kg'].idxmax()} · Mes más flojo: {tabla['kg'].idxmin()}")

    def ver_ranking(self):
        print(self.heladeria.ranking_sabores().to_string())

    def ver_clientes(self):
        h = self.heladeria
        print("Productos vendidos según público (aproximado por tipo de producto):")
        print(h.perfil_clientes().to_string())
        print(f"\nVentas en fin de semana: {h.porcentaje_finde():.1%} → perfil {h.perfil_consumo()}")

    def ver_canales(self):
        print(self.heladeria.ventas_por_canal().to_string())

    def ver_inventario(self):
        inventario = self.heladeria.inventario
        print(inventario)
        print("\nA reponer:")
        print(inventario.a_reponer().to_string())
        print("\nStock que se puede vencer sin usarse:")
        print(inventario.riesgo_vencimiento().to_string())

    def ver_merma(self):
        print("Merma por motivo (costo en pesos de materia prima):")
        print(self.heladeria.merma_por_motivo().to_string())
        print("\nSabores candidatos a salir de carta:")
        print(self.heladeria.sabores_a_discontinuar().to_string())

    def ver_recomendacion(self):
        texto = self.entrada("¿Para qué mes es el lanzamiento? (1 a 12): ").strip()
        if not texto.isdigit():
            raise ValueError("El mes tiene que ser un número del 1 al 12")
        recomendacion = Recomendador(self.heladeria, int(texto)).recomendar()
        print()
        print(recomendacion)