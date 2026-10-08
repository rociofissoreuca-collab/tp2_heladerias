from datos import mostrar_reporte, preparar

carpetas = ["datos/heladeria_centro", "datos/heladeria_barrio"]

for carpeta in carpetas:
    tablas, reporte = preparar(carpeta)
    mostrar_reporte(carpeta, tablas, reporte)