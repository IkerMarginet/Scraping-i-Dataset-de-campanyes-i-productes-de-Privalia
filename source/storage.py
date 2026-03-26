import csv
import os


def save_to_csv(data_list, filepath):
    """
    Guarda una llista de diccionaris en un CSV.
    Sobreescriu el fitxer en cada execució.
    """
    if not data_list:
        print("No hay datos para guardar.")
        return

    headers = list(data_list[0].keys())

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for item in data_list:
            writer.writerow(item)

    print(f"Datos guardados exitosamente en: {filepath}")