"""Clase Comparador: pone varias heladerías lado a lado para compararlas."""
import pandas as pd

from recomendador import Recomendador


class Comparador:
    """Tiene varias heladerías (composición) y arma una tabla con los indicadores clave de cada una."""

    def __init__(self, heladerias):
        if len(heladerias) < 2:
            raise ValueError("Para comparar se necesitan al menos dos heladerías")
        self.heladerias = heladerias

    def indicadores(self, heladeria, mes):
        ventas = heladeria.ventas
        merma = heladeria.merma_con_costo()
        resumen = heladeria.resumen_mensual()
        recomendacion = Recomendador(heladeria, mes).recomendar()
        return {
            "kg vendidos en el año": round(ventas["kg"].sum()),
            "tickets en el año": ventas["id_ticket"].nunique(),
            "ticket promedio de diciembre ($)": resumen["ticket_promedio"].iloc[-1],
            "% de ventas en fin de semana": f"{heladeria.porcentaje_finde():.0%}",
            "perfil": heladeria.perfil_consumo(),
            "público principal": heladeria.publico_principal(),
            "sabor más vendido (kg/día)": heladeria.ranking_sabores().index[0],
            "merma de helado (% de lo vendido)": f"{merma[merma['tipo'] == 'sabor']['cantidad'].sum() / ventas['kg'].sum():.1%}",
            "costo de la merma ($)": round(merma["costo"].sum()),
            "insumos a reponer": len(heladeria.inventario.a_reponer()),
            "insumo estrella": recomendacion.insumo,
            "recomendación": type(recomendacion).__name__.replace("Recomendacion", "").lower(),
        }

    def tabla_comparativa(self, mes=12):
        """Una columna por heladería y una fila por indicador."""
        columnas = {h.nombre: self.indicadores(h, mes) for h in self.heladerias}
        return pd.DataFrame(columnas)