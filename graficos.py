"""Gráficos de la app. Se guardan como imágenes PNG en la carpeta salidas/."""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from heladeria import MESES

COLORES = ["#2a78d6", "#eb6834", "#1baf7a"]
TEXTO = "#52514e"


def preparar_ejes(titulo, etiqueta_x="", etiqueta_y=""):
    figura, ejes = plt.subplots(figsize=(9, 5))
    ejes.set_title(titulo, loc="left", fontsize=13, color="#0b0b0b")
    ejes.set_xlabel(etiqueta_x, color=TEXTO)
    ejes.set_ylabel(etiqueta_y, color=TEXTO)
    ejes.grid(axis="y", alpha=0.25)
    ejes.spines[["top", "right"]].set_visible(False)
    ejes.tick_params(colors=TEXTO)
    return figura, ejes


def guardar(figura, carpeta, nombre_archivo):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    figura.tight_layout()
    figura.savefig(ruta, dpi=120)
    plt.close(figura)
    return ruta


def grafico_estacionalidad(heladerias, carpeta="salidas"):
    """Kg vendidos por mes, una línea por heladería."""
    figura, ejes = preparar_ejes("Kg vendidos por mes", etiqueta_y="kg")
    for numero, heladeria in enumerate(heladerias):
        kg = heladeria.estacionalidad()["kg"]
        color = COLORES[numero % len(COLORES)]
        ejes.plot(range(12), kg.values, color=color, linewidth=2, marker="o", markersize=5, label=heladeria.nombre)
        ejes.annotate(heladeria.nombre, (11, kg.values[-1]), xytext=(6, 0), textcoords="offset points",
                      color=TEXTO, va="center")
    ejes.set_xticks(range(12), [mes[:3] for mes in MESES])
    ejes.set_ylim(bottom=0)
    ejes.legend(frameon=False)
    return guardar(figura, carpeta, "estacionalidad.png")


def grafico_ranking(heladeria, carpeta="salidas", cantidad=10):
    """Los sabores que más venden por día en carta."""
    ranking = heladeria.ranking_sabores().head(cantidad).iloc[::-1]
    figura, ejes = preparar_ejes(f"Heladería {heladeria.nombre}: top {cantidad} sabores", etiqueta_x="kg por día en carta")
    ejes.grid(axis="y", alpha=0)
    ejes.grid(axis="x", alpha=0.25)
    ejes.barh(ranking.index, ranking["kg_por_dia"], color=COLORES[0], height=0.6)
    for posicion, valor in enumerate(ranking["kg_por_dia"]):
        ejes.annotate(f"{valor:.2f}", (valor, posicion), xytext=(4, 0), textcoords="offset points",
                      va="center", color=TEXTO, fontsize=9)
    return guardar(figura, carpeta, f"ranking_{heladeria.nombre.lower()}.png")


def grafico_clientes(heladerias, carpeta="salidas"):
    """Porcentaje de productos vendidos a cada público, por heladería."""
    publicos = ["niños", "adultos", "familias"]
    figura, ejes = preparar_ejes("Productos vendidos según público", etiqueta_y="% de los productos")
    ancho = 0.8 / len(heladerias)
    for numero, heladeria in enumerate(heladerias):
        perfil = heladeria.perfil_clientes().reindex(publicos, fill_value=0) * 100
        posiciones = [p + numero * ancho for p in range(len(publicos))]
        ejes.bar(posiciones, perfil.values, width=ancho * 0.92, color=COLORES[numero % len(COLORES)],
                 label=heladeria.nombre)
        for x, valor in zip(posiciones, perfil.values):
            ejes.annotate(f"{valor:.0f}%", (x, valor), xytext=(0, 3), textcoords="offset points",
                          ha="center", color=TEXTO, fontsize=9)
    ejes.set_xticks([p + ancho * (len(heladerias) - 1) / 2 for p in range(len(publicos))], publicos)
    ejes.legend(frameon=False)
    return guardar(figura, carpeta, "clientes.png")


def grafico_merma(heladeria, carpeta="salidas"):
    """Costo de lo que se tiró, por motivo."""
    merma = heladeria.merma_por_motivo().iloc[::-1]
    figura, ejes = preparar_ejes(f"Heladería {heladeria.nombre}: costo de la merma por motivo",
                                 etiqueta_x="pesos de materia prima")
    ejes.grid(axis="y", alpha=0)
    ejes.grid(axis="x", alpha=0.25)
    ejes.barh(merma.index, merma["costo"], color=COLORES[0], height=0.5)
    for posicion, valor in enumerate(merma["costo"]):
        ejes.annotate(f"${valor:,.0f}".replace(",", "."), (valor, posicion), xytext=(4, 0),
                      textcoords="offset points", va="center", color=TEXTO, fontsize=9)
    return guardar(figura, carpeta, f"merma_{heladeria.nombre.lower()}.png")