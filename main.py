import pandas as pd

from heladeria import Heladeria

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 10)

carpetas = ["datos/heladeria_centro", "datos/heladeria_barrio"]

for carpeta in carpetas:
    heladeria = Heladeria(carpeta)
    print("=" * 70)
    print(heladeria)
    print(f"% de ventas en fin de semana: {heladeria.porcentaje_finde():.1%}")
    print("\nPerfil de clientes:")
    print(heladeria.perfil_clientes().to_string())
    print("\nTop 5 sabores (kg por día en carta):")
    print(heladeria.ranking_sabores().head(5).to_string())
    print("\nEstacionalidad:")
    print(heladeria.estacionalidad().to_string())
    print()