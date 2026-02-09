import os

# La carpeta donde debería estar el libro
ruta_carpeta = r"C:\Users\Robel\Mi unidad\Public\[Libros]\Fernando Leibson Vidal"

print(f"--- EXPLORACIÓN DE CARPETA EN MARIA DELLICIA ---")
if os.path.exists(ruta_carpeta):
    print(f"La carpeta existe. Contenido:")
    for archivo in os.listdir(ruta_carpeta):
        print(f" - {archivo}")
else:
    print("La ruta de la carpeta no es válida o no se encuentra.")
print("--------------------------------------------------")
