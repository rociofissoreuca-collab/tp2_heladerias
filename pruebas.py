import os

import pandas as pd

from datos import es_fecha, es_hora, leer_carpeta, normalizar, preparar, son_meses, verificar_integridad

# 1. Expresiones regulares
assert es_hora("09:30") and es_hora("23:59")
assert not es_hora("25:70") and not es_hora("9:30")
assert es_fecha("2025-12-31")
assert not es_fecha("2025-13-01") and not es_fecha(None)
assert son_meses("6-7-8") and son_meses("12") and son_meses("")
assert not son_meses("6,7,8") and not son_meses("13")

# 2. Normalizar corrige los nombres sin modificar la tabla original
sucia = pd.DataFrame({"sabor": ["  Dulce de LECHE ", "limón"]})
limpia = normalizar(sucia, ["sabor"])
assert list(limpia["sabor"]) == ["dulce de leche", "limón"]
assert sucia["sabor"][0] == "  Dulce de LECHE "

# 3. Integridad: detecta un sabor vendido que no existe en el catálogo
tablas = {
    "ventas": pd.DataFrame({"producto": ["paleta"], "sabor": ["sabor inventado"]}),
    "productos": pd.DataFrame({"producto": ["paleta"], "insumo_envase": ["palito"]}),
    "sabores": pd.DataFrame({"sabor": ["limón"]}),
    "recetas": pd.DataFrame({"sabor": ["limón"], "insumo": ["limón"]}),
    "insumos": pd.DataFrame({"insumo": ["limón", "palito"]}),
    "compras": pd.DataFrame({"insumo": ["limón"]}),
    "merma": pd.DataFrame({"tipo": ["sabor"], "nombre": ["limón"]}),
}
assert verificar_integridad(tablas) == {"sabores vendidos que no están en sabores.csv": ["sabor inventado"]}

# 4. Carpetas inválidas: la app avisa con un error claro en vez de romperse
try:
    leer_carpeta("datos/heladeria_inexistente")
    raise AssertionError("Debía avisar que la carpeta no existe")
except FileNotFoundError:
    pass

try:
    leer_carpeta("datos/Heladeria Centro")
    raise AssertionError("Debía rechazar un nombre de carpeta inválido")
except ValueError:
    pass

os.makedirs("datos/heladeria_incompleta", exist_ok=True)
try:
    leer_carpeta("datos/heladeria_incompleta")
    raise AssertionError("Debía avisar que faltan archivos")
except FileNotFoundError:
    pass
os.rmdir("datos/heladeria_incompleta")

# 5. Flujo completo con los datos de ejemplo
for carpeta in ["datos/heladeria_centro", "datos/heladeria_barrio"]:
    tablas, reporte = preparar(carpeta)
    ventas = tablas["ventas"]
    assert (ventas["cantidad"] > 0).all()
    assert ventas["sabor"].isin(tablas["sabores"]["sabor"]).all()
    assert ventas["producto"].isin(tablas["productos"]["producto"]).all()
    assert "paleta" in list(ventas["producto"]), "'  PALETA ' tenía que normalizarse, no descartarse"
    assert sum(reporte["descartes"]["ventas"].values()) == 4

print("Todas las pruebas pasaron ✔")