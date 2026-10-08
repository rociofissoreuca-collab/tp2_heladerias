"""Clase Inventario: los insumos de una heladería, cuánto se consume, cuánto queda y qué reponer."""
import pandas as pd

DIAS_RECIENTES = 30
MARGEN_SEGURIDAD = 3


def calcular_consumo(ventas, tablas):
    """Consumo de cada insumo por día: helado vendido, helado tirado, envases e insumos tirados."""
    recetas, productos, merma = tablas["recetas"], tablas["productos"], tablas["merma"]

    merma_sabores = merma[merma["tipo"] == "sabor"].rename(columns={"nombre": "sabor", "cantidad": "kg"})
    helado = pd.concat([ventas[["fecha", "sabor", "kg"]], merma_sabores[["fecha", "sabor", "kg"]]])
    por_receta = helado.merge(recetas, on="sabor")
    por_receta["cantidad"] = por_receta["kg"] * por_receta["cantidad_por_kg"]

    productos_vendidos = ventas.drop_duplicates("id_item")
    envases = productos_vendidos.merge(productos[["producto", "insumo_envase"]], on="producto")
    envases = envases.rename(columns={"insumo_envase": "insumo"})

    insumos_tirados = merma[merma["tipo"] == "insumo"].rename(columns={"nombre": "insumo"})

    columnas = ["fecha", "insumo", "cantidad"]
    todo = pd.concat([por_receta[columnas], envases[columnas], insumos_tirados[columnas]])
    return todo.groupby(["fecha", "insumo"])["cantidad"].sum().unstack(fill_value=0)


class Inventario:
    """Los insumos de una heladería. Regla que protege: el stock nunca puede ser negativo."""

    def __init__(self, tablas, ventas, fecha_referencia):
        self._insumos = tablas["insumos"].set_index("insumo")
        self._compras = tablas["compras"]
        self.fecha_referencia = fecha_referencia
        consumo = calcular_consumo(ventas, tablas)
        self._consumo = consumo.reindex(columns=self._insumos.index, fill_value=0)

        negativos = self.stock_actual()[self.stock_actual() < 0]
        if len(negativos) > 0:
            raise ValueError(f"Datos inconsistentes: stock negativo de {', '.join(negativos.index)}")

    def stock_actual(self):
        """Stock actual = stock inicial + compras − consumo."""
        compras = self._compras.groupby("insumo")["cantidad"].sum().reindex(self._insumos.index, fill_value=0)
        consumo = self._consumo.sum()
        return (self._insumos["stock_inicial"] + compras - consumo).round(2)

    def consumo_diario_reciente(self):
        """Consumo promedio por día en los últimos 30 días (refleja la temporada actual)."""
        desde = self.fecha_referencia - pd.Timedelta(DIAS_RECIENTES - 1, unit="D")
        recientes = self._consumo[self._consumo.index >= desde]
        return recientes.sum() / DIAS_RECIENTES

    def dias_cobertura(self):
        """Cuántos días dura el stock actual al ritmo de consumo reciente."""
        consumo = self.consumo_diario_reciente()
        cobertura = self.stock_actual() / consumo.where(consumo > 0)
        return cobertura.round(1)

    def a_reponer(self):
        """Insumos bajo el stock mínimo o que se terminan antes de que llegue un pedido nuevo."""
        tabla = pd.DataFrame({
            "stock_actual": self.stock_actual(),
            "stock_minimo": self._insumos["stock_minimo"],
            "dias_cobertura": self.dias_cobertura(),
            "dias_entrega": self._insumos["dias_entrega"],
        })
        se_usa = self.consumo_diario_reciente() > 0
        bajo_minimo = tabla["stock_actual"] < tabla["stock_minimo"]
        se_termina = tabla["dias_cobertura"] < tabla["dias_entrega"] + MARGEN_SEGURIDAD
        return tabla[se_usa & (bajo_minimo | se_termina)].sort_values("dias_cobertura")

    def frecuencia_pedido(self):
        """Cada cuántos días, en promedio, se compra cada insumo."""
        frecuencia = {}
        for insumo, compras in self._compras.groupby("insumo"):
            fechas = compras["fecha"].sort_values()
            if len(fechas) > 1:
                frecuencia[insumo] = fechas.diff().dt.days.mean()
        return pd.Series(frecuencia, name="dias_entre_pedidos").sort_values().round(1)

    def riesgo_vencimiento(self):
        """Stock que, al ritmo actual, no se va a usar antes de que venza el último lote.

        Incluye los sobrantes de sabores que salieron de carta (consumo 0): ya no se van a usar.
        """
        ultimos = self._compras.sort_values("fecha").groupby("insumo").tail(1).set_index("insumo")
        tabla = pd.DataFrame({
            "vencimiento": ultimos["vencimiento"],
            "dias_para_vencer": (ultimos["vencimiento"] - self.fecha_referencia).dt.days,
            "stock_actual": self.stock_actual(),
            "consumo_diario": self.consumo_diario_reciente(),
        }).dropna(subset=["vencimiento"])
        se_usa_antes = tabla["consumo_diario"] * tabla["dias_para_vencer"].clip(lower=0)
        tabla["en_riesgo"] = (tabla["stock_actual"] - se_usa_antes).clip(lower=0).round(2)
        tabla["vencimiento"] = tabla["vencimiento"].dt.date
        return tabla[tabla["en_riesgo"] > 0].sort_values("dias_para_vencer")

    def es_abastecible(self, insumo, mes):
        """False si el insumo está en temporada de escasez ese mes."""
        texto = self._insumos.loc[insumo, "meses_escasez"]
        if texto == "":
            return True
        meses = [int(numero) for numero in texto.split("-")]
        return mes not in meses

    def __str__(self):
        return f"Inventario de {len(self._insumos)} insumos, {len(self.a_reponer())} para reponer"