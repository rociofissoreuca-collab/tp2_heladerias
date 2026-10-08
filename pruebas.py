import io
import os
from contextlib import redirect_stdout

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
# 8. Merma
merma = centro.merma_con_costo()
assert (merma["costo"] > 0).all(), "Todo lo que se tira tiene un costo"
por_sabor = centro.merma_por_sabor()
cristalizado = merma[(merma["tipo"] == "sabor") & (merma["motivo"] == "cristalizado")]["cantidad"].sum()
assert abs(por_sabor["kg_tirados"].sum() - cristalizado) < 0.01, "Los cortes de luz no cuentan contra el sabor"
assert centro.sabores_a_discontinuar().index[0] == "menta granizada"
assert barrio.sabores_a_discontinuar().index[0] == "menta granizada"
assert "pistacho" not in centro.sabores_a_discontinuar().index, "Las ediciones limitadas no se discontinúan"
# 9. Recomendación: herencia y polimorfismo
from recomendador import Recomendacion, RecomendacionConservadora, RecomendacionInnovadora, Recomendador

for mes_invalido in [0, 13, "julio", 7.5]:
    try:
        Recomendador(centro, mes_invalido)
        raise AssertionError(f"Debía rechazar el mes {mes_invalido!r}")
    except ValueError:
        pass

recomendacion_centro = Recomendador(centro, 12).recomendar()
recomendacion_barrio = Recomendador(barrio, 12).recomendar()
assert isinstance(recomendacion_centro, RecomendacionInnovadora)
assert isinstance(recomendacion_barrio, RecomendacionConservadora)
assert isinstance(recomendacion_centro, Recomendacion) and isinstance(recomendacion_barrio, Recomendacion)
assert recomendacion_centro.insumo == "chispitas de chocolate" and recomendacion_barrio.insumo == "banana"
assert recomendacion_centro.accion() != recomendacion_barrio.accion(), "Cada hija actúa distinto"
assert "pistacho" not in Recomendador(centro, 12).candidatos().index, "Solo insumos de sabores fijos en carta"
assert not Recomendador(barrio, 7).candidatos().loc["frutilla", "abastecible"]

# Filtro de abastecimiento: si las chispitas escasearan en diciembre, se pasa al siguiente insumo
centro_con_escasez = Heladeria("datos/heladeria_centro")
centro_con_escasez.inventario._insumos.loc["chispitas de chocolate", "meses_escasez"] = "12"
insumo, crecimiento, descartados = Recomendador(centro_con_escasez, 12).insumo_estrella()
assert insumo == "galletitas" and descartados == ["chispitas de chocolate"]

try:
    Recomendacion(centro, 12, "cacao", 0.1, [], None, []).accion()
    raise AssertionError("La clase madre no debe definir la acción")
except NotImplementedError:
    pass

# 10. Menú: una sesión completa con entradas válidas e inválidas no rompe la app
from app import App

respuestas = iter(["2", "x", "", "1", "9", "1", "abc", "1", "2",
                   "2", "3", "4", "5", "6", "7", "8", "9", "13", "9", "julio", "9", "12", "10", "11", "0"])
app = App(entrada=lambda mensaje: "" if "Enter" in mensaje else next(respuestas), carpeta_salidas="salidas_prueba")
salida = io.StringIO()
with redirect_stdout(salida):
    app.ejecutar()
texto = salida.getvalue()
assert app.heladeria is not None and app.heladeria.nombre == "Centro"
assert "Primero cargá una heladería" in texto and "Opción inválida" in texto
assert "RECOMENDACIÓN PARA CENTRO" in texto and "¡Hasta luego!" in texto
assert App(carpeta_datos="carpeta_que_no_existe").heladerias_disponibles() == []

# 11. Comparador y gráficos
from comparador import Comparador

try:
    Comparador([centro])
    raise AssertionError("Debía pedir al menos dos heladerías")
except ValueError:
    pass
tabla = Comparador([centro, barrio]).tabla_comparativa()
assert list(tabla.columns) == ["Centro", "Barrio"]
assert tabla.loc["perfil", "Centro"] == "innovadora" and tabla.loc["perfil", "Barrio"] == "conservadora"

graficos_esperados = ["estacionalidad.png", "clientes.png", "ranking_centro.png", "merma_centro.png"]
for archivo in graficos_esperados:
    ruta = os.path.join("salidas_prueba", archivo)
    assert os.path.isfile(ruta), f"El menú debía guardar {archivo}"
    os.remove(ruta)
os.rmdir("salidas_prueba")

print("Todas las pruebas pasaron ✔")