import pandas as pd

from heladeria import Heladeria

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 10)

carpetas = ["datos/heladeria_centro", "datos/heladeria_barrio"]

for carpeta in carpetas:
    heladeria = Heladeria(carpeta)
    inventario = heladeria.inventario
    print("=" * 70)
    print(heladeria)
    print(inventario)
    print(f"% de ventas en fin de semana: {heladeria.porcentaje_finde():.1%}")
    print("\nPerfil de clientes:")
    print(heladeria.perfil_clientes().to_string())
    print("\nTop 5 sabores (kg por día en carta):")
    print(heladeria.ranking_sabores().head(5).to_string())
    print("\nInsumos a reponer:")
    print(inventario.a_reponer().to_string())
    print("\nStock que se puede vencer sin usarse:")
    print(inventario.riesgo_vencimiento().to_string())
    print("\nCada cuántos días se compra cada insumo (los 5 más frecuentes):")
    print(inventario.frecuencia_pedido().head(5).to_string())
    print()