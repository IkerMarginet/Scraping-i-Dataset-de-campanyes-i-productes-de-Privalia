import csv
import os

def save_to_csv(data_list, filepath):
    """
    Guarda una lista de diccionarios en un archivo CSV.
    Crea las cabeceras basándose en las claves del primer diccionario de la lista.
    
    :param data_list: Lista de diccionarios con los datos a guardar.
    :param filepath: Ruta completa donde se guardará el archivo CSV.
    """
    if not data_list:
        print("No hay datos para guardar.")
        return

    # Extraer las cabeceras (nombres de las columnas) a partir de las claves del primer elemento
    headers = list(data_list[0].keys())

    # Comprobar si el archivo ya existe para decidir si escribir las cabeceras
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)

        if not file_exists:
            writer.writeheader()  # Escribir cabeceras solo si el archivo es nuevo
            
        for item in data_list:
            writer.writerow(item)
            
    print(f"Datos guardados exitosamente en: {filepath}")
