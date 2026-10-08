"""Carga, limpieza y validación de los datos de una heladería."""
import os
import re

import pandas as pd

COLUMNAS = {
    "ventas": ["id_ticket", "id_item", "fecha", "hora", "producto", "sabor", "cantidad", "precio_unitario", "canal"],
    "productos": ["producto", "gramos", "max_sabores", "publico", "insumo_envase"],
    "sabores": ["sabor", "categoria", "edicion_limitada", "fecha_alta", "fecha_baja"],
    "recetas": ["sabor", "insumo", "cantidad_por_kg"],
    "insumos": ["insumo", "tipo", "unidad", "stock_inicial", "stock_minimo", "dias_entrega", "meses_escasez"],
    "compras": ["fecha", "insumo", "cantidad", "costo_unitario", "vencimiento"],
    "merma": ["fecha", "tipo", "nombre", "cantidad", "motivo"],
}

COLUMNAS_TEXTO = {
    "ventas": ["producto", "sabor", "canal"],
    "productos": ["producto", "publico", "insumo_envase"],
    "sabores": ["sabor", "categoria", "edicion_limitada"],
    "recetas": ["sabor", "insumo"],
    "insumos": ["insumo", "tipo", "unidad"],
    "compras": ["insumo"],
    "merma": ["tipo", "nombre", "motivo"],
}

COLUMNAS_FECHA = {
    "ventas": ["fecha"],
    "sabores": ["fecha_alta", "fecha_baja"],
    "compras": ["fecha", "vencimiento"],
    "merma": ["fecha"],
}

PATRON_CARPETA = r"heladeria_[a-z0-9_]+"
PATRON_FECHA = r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
PATRON_HORA = r"([01]\d|2[0-3]):[0-5]\d"
PATRON_MESES = r"((1[0-2]|[1-9])(-(1[0-2]|[1-9]))*)?"


def cumple_patron(patron, valor):
    """Devuelve True si el valor completo respeta el patrón."""
    return re.fullmatch(patron, str(valor)) is not None


def es_fecha(valor):
    return cumple_patron(PATRON_FECHA, valor)


def es_hora(valor):
    return cumple_patron(PATRON_HORA, valor)


def son_meses(valor):
    return cumple_patron(PATRON_MESES, valor)


def es_positivo(columna):
    """Convierte la columna a número (lo que no es número queda vacío) y compara con 0."""
    return pd.to_numeric(columna, errors="coerce") > 0


def es_no_negativo(columna):
    return pd.to_numeric(columna, errors="coerce") >= 0


def leer_carpeta(carpeta):
    """Lee los 7 archivos de una heladería y verifica que tengan las columnas necesarias."""
    nombre = os.path.basename(carpeta)
    if not cumple_patron(PATRON_CARPETA, nombre):
        raise ValueError(f"'{nombre}' no es un nombre válido: tiene que ser heladeria_<nombre>, en minúscula")
    if not os.path.isdir(carpeta):
        raise FileNotFoundError(f"No existe la carpeta {carpeta}")

    tablas = {}
    for archivo, columnas in COLUMNAS.items():
        ruta = os.path.join(carpeta, archivo + ".csv")
        if not os.path.isfile(ruta):
            raise FileNotFoundError(f"Falta el archivo {archivo}.csv en {carpeta}")
        tabla = pd.read_csv(ruta, dtype={"hora": str, "meses_escasez": str})
        for columna in columnas:
            if columna not in tabla.columns:
                raise ValueError(f"A {archivo}.csv le falta la columna '{columna}'")
        tablas[archivo] = tabla
    return tablas


def normalizar(tabla, columnas):
    """Devuelve una copia con los textos sin espacios en los extremos y en minúscula."""
    tabla = tabla.copy()
    for columna in columnas:
        tabla[columna] = tabla[columna].str.strip().str.lower()
    return tabla


def descartar(tabla, filas_validas, motivo, descartes):
    """Se queda con las filas válidas y anota cuántas se descartaron por ese motivo."""
    cantidad = int(len(tabla) - filas_validas.sum())
    if cantidad > 0:
        descartes[motivo] = cantidad
    return tabla[filas_validas]


def limpiar_ventas(ventas):
    descartes = {}
    ventas = descartar(ventas, ventas.notna().all(axis=1), "datos faltantes", descartes)
    ventas = descartar(ventas, ventas["fecha"].map(es_fecha), "fecha inválida", descartes)
    ventas = descartar(ventas, ventas["hora"].map(es_hora), "hora inválida", descartes)
    ventas = descartar(ventas, es_positivo(ventas["cantidad"]), "cantidad no positiva", descartes)
    ventas = descartar(ventas, es_positivo(ventas["precio_unitario"]), "precio no positivo", descartes)
    return ventas, descartes


def limpiar_productos(productos):
    descartes = {}
    productos = descartar(productos, es_positivo(productos["gramos"]), "gramos no positivos", descartes)
    productos = descartar(productos, es_positivo(productos["max_sabores"]), "máximo de sabores no positivo", descartes)
    return productos, descartes


def limpiar_sabores(sabores):
    descartes = {}
    sabores = descartar(sabores, sabores["fecha_alta"].map(es_fecha), "fecha de alta inválida", descartes)
    baja_valida = sabores["fecha_baja"].isna() | sabores["fecha_baja"].map(es_fecha)
    sabores = descartar(sabores, baja_valida, "fecha de baja inválida", descartes)
    sabores = descartar(sabores, sabores["edicion_limitada"].isin(["si", "no"]), "edición limitada distinta de si/no", descartes)
    return sabores, descartes


def limpiar_recetas(recetas):
    descartes = {}
    recetas = descartar(recetas, es_positivo(recetas["cantidad_por_kg"]), "cantidad por kg no positiva", descartes)
    return recetas, descartes


def limpiar_insumos(insumos):
    descartes = {}
    insumos = insumos.copy()
    insumos["meses_escasez"] = insumos["meses_escasez"].fillna("")
    insumos = descartar(insumos, insumos["tipo"].isin(["base", "distintivo", "envase"]), "tipo desconocido", descartes)
    insumos = descartar(insumos, insumos["meses_escasez"].map(son_meses), "meses de escasez mal escritos", descartes)
    stock_valido = es_no_negativo(insumos["stock_inicial"]) & es_no_negativo(insumos["stock_minimo"])
    insumos = descartar(insumos, stock_valido, "stock negativo", descartes)
    insumos = descartar(insumos, es_no_negativo(insumos["dias_entrega"]), "días de entrega negativos", descartes)
    return insumos, descartes


def limpiar_compras(compras):
    descartes = {}
    fechas_validas = compras["fecha"].map(es_fecha) & compras["vencimiento"].map(es_fecha)
    compras = descartar(compras, fechas_validas, "fecha inválida", descartes)
    compras = descartar(compras, es_positivo(compras["cantidad"]), "cantidad no positiva", descartes)
    compras = descartar(compras, es_positivo(compras["costo_unitario"]), "costo no positivo", descartes)
    return compras, descartes


def limpiar_merma(merma):
    descartes = {}
    merma = descartar(merma, merma["fecha"].map(es_fecha), "fecha inválida", descartes)
    merma = descartar(merma, merma["tipo"].isin(["sabor", "insumo"]), "tipo distinto de sabor/insumo", descartes)
    merma = descartar(merma, es_positivo(merma["cantidad"]), "cantidad no positiva", descartes)
    return merma, descartes


LIMPIEZAS = {
    "ventas": limpiar_ventas,
    "productos": limpiar_productos,
    "sabores": limpiar_sabores,
    "recetas": limpiar_recetas,
    "insumos": limpiar_insumos,
    "compras": limpiar_compras,
    "merma": limpiar_merma,
}


def nombres_faltantes(usados, catalogo):
    """Devuelve los nombres que se usan en una tabla pero no existen en el catálogo."""
    return sorted(set(usados) - set(catalogo))


def verificar_integridad(tablas):
    """Revisa que los nombres usados en cada tabla existan en su catálogo."""
    ventas, productos, sabores = tablas["ventas"], tablas["productos"], tablas["sabores"]
    recetas, insumos, compras, merma = tablas["recetas"], tablas["insumos"], tablas["compras"], tablas["merma"]
    controles = [
        ("productos vendidos que no están en productos.csv", ventas["producto"], productos["producto"]),
        ("sabores vendidos que no están en sabores.csv", ventas["sabor"], sabores["sabor"]),
        ("sabores sin receta", sabores["sabor"], recetas["sabor"]),
        ("insumos de recetas que no están en insumos.csv", recetas["insumo"], insumos["insumo"]),
        ("envases que no están en insumos.csv", productos["insumo_envase"], insumos["insumo"]),
        ("insumos comprados que no están en insumos.csv", compras["insumo"], insumos["insumo"]),
        ("sabores en merma que no están en sabores.csv", merma[merma["tipo"] == "sabor"]["nombre"], sabores["sabor"]),
        ("insumos en merma que no están en insumos.csv", merma[merma["tipo"] == "insumo"]["nombre"], insumos["insumo"]),
    ]
    problemas = {}
    for descripcion, usados, catalogo in controles:
        faltan = nombres_faltantes(usados, catalogo)
        if faltan:
            problemas[descripcion] = faltan
    return problemas


def quitar_ventas_invalidas(ventas, productos, sabores):
    """Saca las ventas de productos o sabores que no existen y los productos con más sabores de los permitidos."""
    descartes = {}
    ventas = descartar(ventas, ventas["producto"].isin(productos["producto"]), "producto fuera de catálogo", descartes)
    ventas = descartar(ventas, ventas["sabor"].isin(sabores["sabor"]), "sabor fuera de catálogo", descartes)
    maximo = dict(zip(productos["producto"], productos["max_sabores"]))
    sabores_por_item = ventas["id_item"].map(ventas["id_item"].value_counts())
    ventas = descartar(ventas, sabores_por_item <= ventas["producto"].map(maximo), "más sabores que los permitidos", descartes)
    return ventas, descartes


def preparar(carpeta):
    """Flujo completo: leer → normalizar → limpiar → verificar integridad → convertir fechas."""
    tablas = leer_carpeta(carpeta)
    descartes = {}
    for nombre in tablas:
        tabla = normalizar(tablas[nombre], COLUMNAS_TEXTO[nombre])
        tablas[nombre], descartes[nombre] = LIMPIEZAS[nombre](tabla)

    integridad = verificar_integridad(tablas)
    tablas["ventas"], descartes_catalogo = quitar_ventas_invalidas(tablas["ventas"], tablas["productos"], tablas["sabores"])
    descartes["ventas"].update(descartes_catalogo)

    for nombre, columnas in COLUMNAS_FECHA.items():
        for columna in columnas:
            tablas[nombre][columna] = pd.to_datetime(tablas[nombre][columna], format="%Y-%m-%d")
    for nombre in tablas:
        tablas[nombre] = tablas[nombre].reset_index(drop=True)

    return tablas, {"descartes": descartes, "integridad": integridad}


def mostrar_reporte(carpeta, tablas, reporte):
    print(f"Heladería: {os.path.basename(carpeta)}")
    for nombre, tabla in tablas.items():
        print(f"  {nombre}: {len(tabla)} filas válidas")
    for nombre, motivos in reporte["descartes"].items():
        for motivo, cantidad in motivos.items():
            print(f"  ⚠ {nombre}: {cantidad} fila(s) descartada(s) por {motivo}")
    for problema, nombres in reporte["integridad"].items():
        print(f"  ⚠ {problema}: {', '.join(nombres)}")
    print()