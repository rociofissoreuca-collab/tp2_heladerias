"""Clase Heladeria: una heladería con sus ventas ya limpias, y las preguntas que responde sobre ellas."""
import os

import pandas as pd

from datos import preparar
from inventario import Inventario

UMBRAL_CONSERVADOR = 0.45
MOTIVOS_ACCIDENTALES = ["corte de luz"]
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

    def ventas_por_canal(self):
        """Qué parte de los productos y de la facturación entra por cada canal (salón, para llevar, delivery)."""
        productos_vendidos = self._ventas.drop_duplicates("id_item")
        unidades = productos_vendidos.groupby("canal")["cantidad"].sum()
        facturacion = self._ventas.groupby("canal")["importe"].sum()
        tabla = (unidades / unidades.sum()).to_frame("productos")
        tabla["facturacion"] = facturacion / facturacion.sum()
        return tabla.sort_values("productos", ascending=False).round(3)

    def merma_con_costo(self):
        """Cada registro de merma con su costo en pesos, usando el costo de los insumos de ese mes."""
        merma = self.tablas["merma"].reset_index().rename(columns={"index": "id"})
        merma["mes"] = merma["fecha"].dt.month
        costos = self.inventario.costo_mensual().stack().reset_index(name="costo_unitario")

        recetas = self.tablas["recetas"].rename(columns={"sabor": "nombre"})
        de_sabores = merma[merma["tipo"] == "sabor"].merge(recetas, on="nombre")
        de_sabores["cantidad_insumo"] = de_sabores["cantidad"] * de_sabores["cantidad_por_kg"]
        de_insumos = merma[merma["tipo"] == "insumo"].copy()
        de_insumos["insumo"] = de_insumos["nombre"]
        de_insumos["cantidad_insumo"] = de_insumos["cantidad"]

        columnas = ["id", "mes", "insumo", "cantidad_insumo"]
        detalle = pd.concat([de_sabores[columnas], de_insumos[columnas]]).merge(costos, on=["mes", "insumo"])
        detalle["costo"] = detalle["cantidad_insumo"] * detalle["costo_unitario"]
        merma["costo"] = merma["id"].map(detalle.groupby("id")["costo"].sum()).fillna(0).round(0)
        return merma.drop(columns="id")

    def merma_por_motivo(self):
        """Cuántas veces, cuántos kg y cuánta plata se tiró por cada motivo."""
        merma = self.merma_con_costo()
        resumen = merma.groupby("motivo").agg(
            registros=("cantidad", "count"),
            kg=("cantidad", "sum"),
            costo=("costo", "sum"),
        )
        return resumen.sort_values("costo", ascending=False).round(1)

    def merma_por_sabor(self):
        """Kg de helado tirado por sabor y qué parte de lo que vende representa (sin contar accidentes)."""
        merma = self.merma_con_costo()
        evitable = merma[(merma["tipo"] == "sabor") & (~merma["motivo"].isin(MOTIVOS_ACCIDENTALES))]
        resumen = evitable.groupby("nombre").agg(kg_tirados=("cantidad", "sum"), costo=("costo", "sum"))
        resumen.index.name = "sabor"
        kg_vendidos = self._ventas.groupby("sabor")["kg"].sum()
        resumen["merma_sobre_ventas"] = resumen["kg_tirados"] / kg_vendidos
        return resumen.sort_values("merma_sobre_ventas", ascending=False).round(3)

    def sabores_a_discontinuar(self):
        """Sabores fijos en carta que venden poco y se tiran mucho: candidatos a dejar su lugar."""
        ranking = self.ranking_sabores()
        merma = self.merma_por_sabor()
        tabla = ranking.join(merma[["kg_tirados", "merma_sobre_ventas"]]).fillna({"kg_tirados": 0, "merma_sobre_ventas": 0})
        en_carta = self.tablas["sabores"].set_index("sabor")["fecha_baja"].isna()
        tabla = tabla[en_carta.reindex(tabla.index) & (tabla["edicion_limitada"] == "no")]

        vende_poco = tabla["kg_por_dia"] < tabla["kg_por_dia"].quantile(0.25)
        se_tira_mucho = tabla["merma_sobre_ventas"] > tabla["merma_sobre_ventas"].median()
        candidatos = tabla[vende_poco & se_tira_mucho]
        return candidatos[["kg_por_dia", "kg_tirados", "merma_sobre_ventas"]].sort_values("merma_sobre_ventas", ascending=False)

    def __str__(self):
        return (f"Heladería {self.nombre}: {self._ventas['kg'].sum():,.0f} kg vendidos, "
                f"perfil {self.perfil_consumo()}, público principal: {self.publico_principal()}")