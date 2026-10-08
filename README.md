# Analizador de heladerías

Herramienta de apoyo a la decisión para heladerías. Cada heladería carga sus datos de ventas, insumos, compras y merma, y la app le recomienda qué sabor agregar, qué sabor sacar, qué insumos reponer y quién es su cliente. También permite comparar heladerías entre sí.

**Autora:** Rocío Fissore — Programación Orientada a Datos con Python, UCA Rosario

## Flujo de datos

| Etapa | En la app |
|---|---|
| Datos crudos | Un CSV por tabla, en una carpeta por heladería |
| Limpieza | `datos.py`: normaliza nombres, valida formatos con expresiones regulares, descarta filas inválidas y verifica que los nombres coincidan entre tablas |
| Transformación | *(próxima etapa)* |
| Análisis | *(próxima etapa)* |
| Visualización | *(próxima etapa)* |
| Interpretación | *(próxima etapa)* |

## Estructura

| Archivo | Rol |
|---|---|
| `datos.py` | Carga, limpieza y validación (funciones puras, salvo la lectura de archivos) |
| `main.py` | Punto de entrada |
| `pruebas.py` | Verificaciones con `assert`, incluidos los casos límite |

## Datos

Cada heladería es una carpeta `datos/heladeria_<nombre>/` con 7 archivos:

| Archivo | Una fila es… |
|---|---|
| `ventas.csv` | un sabor dentro de un producto vendido (los sabores de un mismo producto comparten `id_item`) |
| `productos.csv` | un producto del catálogo |
| `sabores.csv` | un sabor del catálogo |
| `recetas.csv` | un insumo de un sabor, por kg de helado |
| `insumos.csv` | un insumo (base, distintivo o envase) |
| `compras.csv` | un lote de insumo comprado |
| `merma.csv` | algo que se tiró |

Los datos son **simulados**, con la estructura que exportaría el sistema de caja de una heladería real.

Las dos heladerías de ejemplo tienen perfiles opuestos a propósito:
- **Centro:** ventas repartidas en la semana y público mayormente adulto.
- **Barrio:** ventas concentradas en el fin de semana y público mayormente familiar.

Los datos incluyen algunos errores de carga intencionales (hora inválida, cantidad negativa, sabor inexistente, fecha faltante, nombres con mayúsculas y espacios) para mostrar la limpieza.

## Cómo ejecutar

```bash
pip install -r requirements.txt
python pruebas.py
python main.py
```

## Supuestos

- Producción = ventas + merma: los insumos se consumen al fabricar el helado.
- El stock cumple siempre: stock final = stock inicial + compras − consumo por ventas − consumo por merma.
- Precios y costos se registran en cada venta y compra, porque cambian con la inflación.