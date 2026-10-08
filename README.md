# Analizador de heladerías

Herramienta de apoyo a la decisión para heladerías. Cada heladería carga sus datos de ventas, insumos, compras y merma, y la app le dice **qué sabor agregar, qué sabor sacar, qué insumos reponer y quién es su cliente**. También compara heladerías entre sí.

**Autora:** Rocío Fissore. Programación Orientada a Datos con Python, UCA Rosario.

## Cómo ejecutar

```bash
pip install -r requirements.txt
python main.py        # abre el menú
python pruebas.py     # corre todas las verificaciones
```

## Menú

| Opción | Qué muestra |
|---|---|
| 1 | Cargar una heladería (elegís de la lista de carpetas en `datos/`) |
| 2 | Resumen de ventas por mes: kg, facturación, tickets y ticket promedio |
| 3 | Estacionalidad: kg por mes e índice estacional |
| 4 | Ranking de sabores en kg por día en carta |
| 5 | Público (según tipo de producto) y perfil de consumo (innovadora / conservadora) |
| 6 | Ventas por canal (salón, para llevar, delivery) |
| 7 | Inventario: qué reponer y qué stock se puede vencer sin usarse |
| 8 | Merma por motivo y sabores candidatos a salir de carta |
| 9 | Recomendación del próximo sabor para el mes que elijas |
| 10 | Comparación de todas las heladerías, con gráficos |
| 11 | Gráficos de la heladería cargada (se guardan en `salidas/`) |
| 0 | Salir |

La app no se cierra ante entradas inválidas: opciones que no existen, letras en vez de números, un mes fuera de rango o un análisis pedido antes de cargar una heladería se responden con un aviso y se vuelve al menú.

## Flujo de datos

| Etapa | En la app |
|---|---|
| Datos crudos | Un CSV por tabla, en una carpeta por heladería |
| Limpieza | `datos.py`: normaliza nombres, valida formatos con expresiones regulares, descarta filas inválidas contando el motivo y verifica que los nombres coincidan entre tablas |
| Transformación | `heladeria.py` (kg e importe de cada sabor vendido) e `inventario.py` (consumo diario de cada insumo) |
| Análisis | `Heladeria`, `Inventario`, `Recomendador` y `Comparador` |
| Visualización | `graficos.py` |
| Interpretación | La `Recomendacion`, en palabras y con los números que la justifican |

## Estructura

| Archivo | Rol |
|---|---|
| `main.py` | Punto de entrada: crea la `App` y la ejecuta |
| `app.py` | Clase `App`: menú con `input()` y manejo de errores |
| `datos.py` | Carga, limpieza y validación (funciones puras, salvo la lectura de archivos) |
| `heladeria.py` | Clase `Heladeria`: ventas, clientes, estacionalidad y merma |
| `inventario.py` | Clase `Inventario`: stock, reposición, vencimientos, costos y crecimiento del consumo |
| `recomendador.py` | Clase `Recomendador` y la jerarquía `Recomendacion` → `RecomendacionInnovadora` / `RecomendacionConservadora` |
| `comparador.py` | Clase `Comparador`: tabla de indicadores lado a lado |
| `graficos.py` | Gráficos con matplotlib |
| `pruebas.py` | Verificaciones con `assert`, incluidos los casos límite y una sesión simulada del menú |

## Diseño orientado a objetos

```
App ──usa──> Heladeria ──tiene un──> Inventario
 │               ▲
 │               └──usa── Recomendador ──crea──> Recomendacion
 │                                                ├── RecomendacionInnovadora
 └──usa──> Comparador ──tiene varias──> Heladeria └── RecomendacionConservadora
```

- **Composición:** la `Heladeria` tiene un `Inventario`; el `Comparador` tiene varias heladerías.
- **Herencia y polimorfismo:** las dos recomendaciones heredan de `Recomendacion` y sobrescriben `accion()`. `print(recomendacion)` funciona igual para las dos, pero cada una propone algo distinto.
- **Encapsulamiento:** los datos internos llevan guion bajo (`_ventas`, `_insumos`). `ventas` es una `@property` que devuelve una copia.
- **Invariante:** el `Inventario` no se crea si los datos dan stock negativo.

## Datos

Cada heladería es una carpeta `datos/heladeria_<nombre>/` con 7 archivos:

| Archivo | Una fila es… |
|---|---|
| `ventas.csv` | un sabor dentro de un producto vendido (los sabores de un mismo producto comparten `id_item`) |
| `productos.csv` | un producto del catálogo, con gramos, máximo de sabores, público y envase |
| `sabores.csv` | un sabor, con categoría, edición limitada, fecha de alta y de baja |
| `recetas.csv` | un insumo de un sabor, por kg de helado |
| `insumos.csv` | un insumo (base, distintivo o envase), con stock inicial, stock mínimo, días de entrega y meses de escasez |
| `compras.csv` | un lote de insumo comprado, con costo y vencimiento |
| `merma.csv` | algo que se tiró, con el motivo |

Los datos son **simulados**, con la estructura que exportaría el sistema de caja de una heladería real. Las dos heladerías de ejemplo tienen perfiles opuestos a propósito:
- **Centro:** ventas repartidas en la semana y público mayormente adulto → recomendación innovadora.
- **Barrio:** ventas concentradas en el fin de semana y público mayormente familiar → recomendación conservadora.

Incluyen errores de carga intencionales (hora inválida, cantidad negativa, sabor inexistente, fecha faltante, nombres con mayúsculas y espacios) para mostrar la limpieza.

## Decisiones de medición

| Qué | Cómo | Por qué |
|---|---|---|
| Estacionalidad | kg por mes | En pesos, la inflación inflaría los últimos meses |
| Facturación y ticket | Por mes | Por la inflación, un promedio anual en pesos no tiene sentido |
| Ranking de sabores | kg por día en carta | Para no castigar a las ediciones limitadas |
| Público | Tipo de producto (paleta → niños, 1 kg → familias) | La heladería no registra la edad: es un indicador aproximado |
| Perfil innovador / conservador | % de kg en fin de semana, mes a mes; más de 45% = conservadora | Con ventas parejas sería 2/7 ≈ 29% |
| Insumo estrella | Crecimiento del consumo por kg vendido, 2.º vs. 1.er semestre, entre los insumos distintivos de sabores fijos en carta | Las unidades de los insumos no son comparables; dividir por kg saca el efecto del verano |
| Abastecimiento | Filtro: si el insumo escasea en el mes elegido, se pasa al siguiente | |
| Reposición | Días de cobertura (stock ÷ consumo de los últimos 30 días) contra días de entrega + 3 | Refleja la temporada actual |
| Sabor a sacar | Está en el 25% que menos vende por día y tira más que la mediana; sin contar cortes de luz | Un accidente no es culpa del sabor |

## Supuestos

- Producción = ventas + merma: los insumos se consumen al fabricar el helado.
- El stock cumple siempre: stock final = stock inicial + compras − consumo por ventas − consumo por merma.
- Precios y costos se registran en cada venta y compra, porque cambian con la inflación.
- "Hoy" es la última fecha del dataset.
- Consumo diario parejo = clientes frecuentes (sin registro de clientes no se puede verificar).