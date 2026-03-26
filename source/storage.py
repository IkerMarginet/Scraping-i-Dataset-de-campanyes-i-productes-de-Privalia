import csv
import os


def save_to_csv(data_list, filepath):
    """
    Guarda una llista de diccionaris en un CSV.
    Sobreescriu el fitxer en cada execució.
    """
    if not data_list:
        print("No hi ha dades per desar.")
        return

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    all_headers = set()
    for item in data_list:
        all_headers.update(item.keys())

    preferred_order = [
        "campaign_name",
        "campaign_sector",
        "campaign_end_date",
        "product_name",
        "product_url",
        "original_price",
        "discount_price",
        "discount_percentage",
        "color",
        "available_sizes",
        "description",
    ]

    remaining_headers = [h for h in sorted(all_headers) if h not in preferred_order]
    headers = [h for h in preferred_order if h in all_headers] + remaining_headers

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()

        for item in data_list:
            row = {header: item.get(header, "") for header in headers}
            writer.writerow(row)

    print(f"Dades desades correctament a: {filepath}")