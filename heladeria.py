"""Clase Heladeria: una heladería con sus ventas ya limpias, y las preguntas que responde sobre ellas."""
import os

from datos import preparar
from inventario import Inventario

UMBRAL_CONSERVADOR = 0.45
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def agregar_columnas(ventas, productos):
    """Cruza las ventas con los productos y calcula los kg y el importe de cada sabor vendido."""
    tabla = ventas.merge(productos[["producto", "gramos", "publico"]], on="producto")
    sabores_por_item = tabla["id_item"].map(tabla["id_item"].value_counts())
    tabla["kg"] = tabla["gramos"] / 1000 / sabores_por_item * tabla["cantidad"]
    tabla["importe"] = tabla["precio_unitario"] / sabores_por_item * tabla["cantidad"]
    tabla["mes"] = tabla["fecha"].dt.month
    tabla["es_finde"] = tabla["fecha"].dt.dayofweek >= 5
    return tabla


class Heladeria:
    """Una heladería: carga sus datos al crearse y responde preguntas sobre sus ventas y clientes."""

    def __init__(self, carpeta):
        tablas, reporte = preparar(carpeta)
        self.nombre = os.path.basename(carpeta).replace("heladeria_", "").capitalize()
        self.reporte = reporte
        self.tablas = tablas
        self._ventas = agregar_columnas(tablas["ventas"], tablas["productos"])
        self.fecha_inicio = self._ventas["fecha"].min()
        self.fecha_referencia = self._ventas["fecha"].max()
        self.inventario = Inventario(tablas, self._ventas, self.fecha_referencia)

    @property
    def ventas(self):
        """Devuelve una copia, para que nadie modifique las ventas desde afuera."""
        return self._ventas.copy()

    def resumen_mensual(self):
        """Kg vendidos, facturación, cantidad de tickets y ticket promedio de cada mes."""
        resumen = self._ventas.groupby("mes").agg(
            kg=("kg", "sum"),
            facturacion=("importe", "sum"),
            tickets=("id_ticket", "nunique"),
        )
        resumen["ticket_promedio"] = resumen["facturacion"] / resumen["tickets"]
        resumen.index = [MESES[mes - 1] for mes in resumen.index]
        return resumen.round(1)

    def estacionalidad(self):
        """Kg vendidos por mes y cuánto se aleja cada mes del promedio (1 = un mes promedio)."""
        kg_por_mes = self.resumen_mensual()["kg"]
        indice = kg_por_mes / kg_por_mes.mean()
        return kg_por_mes.to_frame().assign(indice=indice.round(2))

    def ranking_sabores(self):
        """Kg vendidos por día en carta, para no castigar a las ediciones limitadas."""
        sabores = self.tablas["sabores"].copy()
        inicio = sabores["fecha_alta"].clip(lower=self.fecha_inicio)
        fin = sabores["fecha_baja"].fillna(self.fecha_referencia).clip(upper=self.fecha_referencia)
        sabores["dias_en_carta"] = (fin - inicio).dt.days + 1

        kg_por_sabor = self._ventas.groupby("sabor")["kg"].sum()
        ranking = sabores.set_index("sabor")[["categoria", "edicion_limitada", "dias_en_carta"]]
        ranking["kg_totales"] = kg_por_sabor
        ranking["kg_por_dia"] = ranking["kg_totales"] / ranking["dias_en_carta"]
        return ranking.sort_values("kg_por_dia", ascending=False).round(2)

    def perfil_clientes(self):
        """Porcentaje de productos vendidos a cada público (según el tipo de producto)."""
        productos_vendidos = self._ventas.drop_duplicates("id_item")
        unidades = productos_vendidos.groupby("publico")["cantidad"].sum()
        return (unidades / unidades.sum()).sort_values(ascending=False).round(3)

    def publico_principal(self):
        return self.perfil_clientes().index[0]

    def porcentaje_finde(self):
        """Promedio, mes a mes, del % de kg vendidos en fin de semana."""
        kg = self._ventas.groupby(["mes", "es_finde"])["kg"].sum().unstack(fill_value=0)
        por_mes = kg[True] / (kg[True] + kg[False])
        return round(por_mes.mean(), 3)

    def perfil_consumo(self):
        """Conservadora si concentra mucho en el fin de semana; innovadora si vende parejo."""
        if self.porcentaje_finde() > UMBRAL_CONSERVADOR:
            return "conservadora"
        return "innovadora"

    def __str__(self):
        return (f"Heladería {self.nombre}: {self._ventas['kg'].sum():,.0f} kg vendidos, "
                f"perfil {self.perfil_consumo()}, público principal: {self.publico_principal()}")