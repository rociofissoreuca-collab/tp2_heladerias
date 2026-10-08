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
# 6. Clase Heladeria
from heladeria import Heladeria

centro = Heladeria("datos/heladeria_centro")
barrio = Heladeria("datos/heladeria_barrio")

assert centro.nombre == "Centro"
assert centro.perfil_consumo() == "innovadora" and barrio.perfil_consumo() == "conservadora"
assert centro.publico_principal() == "adultos" and barrio.publico_principal() == "familias"
assert abs(centro.perfil_clientes().sum() - 1) < 0.01, "Los porcentajes de público tienen que sumar 100%"

# La facturación tiene que coincidir con la de los tickets originales
productos_vendidos = centro.tablas["ventas"].drop_duplicates("id_item")
facturacion_original = (productos_vendidos["precio_unitario"] * productos_vendidos["cantidad"]).sum()
assert abs(centro.resumen_mensual()["facturacion"].sum() - facturacion_original) < 1

# Encapsulamiento: modificar la copia no cambia las ventas de la heladería
copia = centro.ventas
copia["kg"] = 0
assert centro.ventas["kg"].sum() > 0
# 7. Clase Inventario
from inventario import Inventario

inventario = centro.inventario
assert (inventario.stock_actual() >= 0).all(), "El stock nunca puede ser negativo"
assert not inventario.es_abastecible("frutilla", 7), "En julio la frutilla está en escasez"
assert inventario.es_abastecible("frutilla", 12) and inventario.es_abastecible("cacao", 7)
assert (inventario.a_reponer()["dias_cobertura"] > 0).all(), "No se piden insumos que ya no se usan"

# Si los datos no cierran (sin stock inicial ni compras), el inventario lo detecta
tablas_rotas = dict(centro.tablas)
tablas_rotas["insumos"] = centro.tablas["insumos"].assign(stock_inicial=0)
tablas_rotas["compras"] = centro.tablas["compras"].iloc[0:0]
try:
    Inventario(tablas_rotas, centro.ventas, centro.fecha_referencia)
    raise AssertionError("Debía detectar stock negativo")
except ValueError:
    pass

print("Todas las pruebas pasaron ✔")