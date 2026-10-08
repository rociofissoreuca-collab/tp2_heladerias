"""Recomendación del próximo sabor: Recomendador arma los datos y elige qué tipo de Recomendacion crear."""
from heladeria import MESES

IDEAS_POR_PUBLICO = {
    "niños": "un sabor dulce y con agregados (confites, cookies, salsa)",
    "adultos": "una versión más intensa o premium",
    "familias": "un clásico de sabor amigable que guste a todas las edades",
}


class Recomendacion:
    """Lo que tienen en común las dos recomendaciones. Cada hija define qué acción proponer."""

    def __init__(self, heladeria, mes, insumo, crecimiento, sabores_con_insumo, sabor_debil, descartados):
        self.heladeria = heladeria
        self.mes = mes
        self.insumo = insumo
        self.crecimiento = crecimiento
        self.sabores_con_insumo = sabores_con_insumo
        self.sabor_debil = sabor_debil
        self.descartados = descartados

    def accion(self):
        raise NotImplementedError("Cada tipo de recomendación define su propia acción")

    def accion_sabor_debil(self):
        raise NotImplementedError("Cada tipo de recomendación define qué hacer con el sabor débil")

    def justificacion(self):
        h = self.heladeria
        publico = h.publico_principal()
        lineas = [
            f"Insumo estrella: {self.insumo}. Su uso por kg vendido creció {self.crecimiento:.0%} "
            f"en el 2.º semestre (lo llevan: {', '.join(self.sabores_con_insumo)}).",
            f"Está disponible en {MESES[self.mes - 1]}.",
            f"Perfil {h.perfil_consumo()}: {h.porcentaje_finde():.0%} de las ventas son en fin de semana.",
            f"Público principal: {publico} ({h.perfil_clientes()[publico]:.0%} de los productos vendidos).",
        ]
        for insumo in self.descartados:
            lineas.append(f"Se descartó {insumo}: hay escasez en {MESES[self.mes - 1]}.")
        return lineas

    def __str__(self):
        lineas = [f"RECOMENDACIÓN PARA {self.heladeria.nombre.upper()} — {MESES[self.mes - 1]}", ""]
        lineas += ["Por qué:"] + [f"  • {linea}" for linea in self.justificacion()]
        lineas += ["", f"Qué hacer: {self.accion()}"]
        if self.sabor_debil is not None:
            lineas.append(f"Sabor débil: {self.accion_sabor_debil()}")
        return "\n".join(lineas)


class RecomendacionInnovadora(Recomendacion):
    """Para heladerías con clientes frecuentes: conviene sacar algo nuevo."""

    def accion(self):
        idea = IDEAS_POR_PUBLICO[self.heladeria.publico_principal()]
        return f"lanzar una edición limitada con {self.insumo}: {idea}."

    def accion_sabor_debil(self):
        return f"sacar {self.sabor_debil} de la carta para hacerle lugar al nuevo sabor en la batea."


class RecomendacionConservadora(Recomendacion):
    """Para heladerías de consumo ocasional: conviene reforzar lo que ya funciona."""

    def accion(self):
        sabores = " y ".join(self.sabores_con_insumo[:2])
        return f"no lanzar un sabor nuevo; producir más {sabores} y asegurar stock de {self.insumo}."

    def accion_sabor_debil(self):
        return f"producir menos cantidad de {self.sabor_debil} para reducir lo que se tira."


class Recomendador:
    """Usa los datos de una heladería para elegir el insumo estrella y el tipo de recomendación."""

    def __init__(self, heladeria, mes):
        if not isinstance(mes, int) or not 1 <= mes <= 12:
            raise ValueError("El mes tiene que ser un número entero entre 1 y 12")
        self.heladeria = heladeria
        self.mes = mes

    def sabores_fijos_en_carta(self):
        sabores = self.heladeria.tablas["sabores"]
        fijos = sabores[sabores["fecha_baja"].isna() & (sabores["edicion_limitada"] == "no")]
        return list(fijos["sabor"])

    def candidatos(self):
        """Insumos distintivos que usan los sabores fijos en carta, ordenados por crecimiento."""
        h, inventario = self.heladeria, self.heladeria.inventario
        recetas = h.tablas["recetas"]
        insumos = h.tablas["insumos"].set_index("insumo")
        en_uso = set(recetas[recetas["sabor"].isin(self.sabores_fijos_en_carta())]["insumo"])
        distintivos = [i for i in insumos.index if insumos.loc[i, "tipo"] == "distintivo" and i in en_uso]

        kg_por_dia = h.ventas.groupby("fecha")["kg"].sum()
        tabla = inventario.crecimiento_consumo(kg_por_dia)[distintivos].to_frame("crecimiento")
        tabla["abastecible"] = [inventario.es_abastecible(insumo, self.mes) for insumo in tabla.index]
        return tabla.sort_values("crecimiento", ascending=False)

    def insumo_estrella(self):
        """El de mayor crecimiento entre los que se consiguen ese mes, y los que se descartaron antes."""
        descartados = []
        for insumo, fila in self.candidatos().iterrows():
            if fila["abastecible"]:
                return insumo, fila["crecimiento"], descartados
            descartados.append(insumo)
        raise ValueError(f"Ningún insumo distintivo se consigue en {MESES[self.mes - 1]}")

    def sabores_con(self, insumo):
        """Sabores fijos en carta que llevan el insumo, del más vendido al menos vendido."""
        recetas = self.heladeria.tablas["recetas"]
        lo_usan = set(recetas[recetas["insumo"] == insumo]["sabor"]) & set(self.sabores_fijos_en_carta())
        ranking = self.heladeria.ranking_sabores()
        return [sabor for sabor in ranking.index if sabor in lo_usan]

    def recomendar(self):
        insumo, crecimiento, descartados = self.insumo_estrella()
        debiles = self.heladeria.sabores_a_discontinuar()
        sabor_debil = debiles.index[0] if len(debiles) > 0 else None
        datos = (self.heladeria, self.mes, insumo, crecimiento, self.sabores_con(insumo), sabor_debil, descartados)
        if self.heladeria.perfil_consumo() == "innovadora":
            return RecomendacionInnovadora(*datos)
        return RecomendacionConservadora(*datos)