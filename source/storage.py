import csv
import os


def save_campaigns(campaigns_list, filepath):
    if not campaigns_list:
        return

    headers = [
        "campaign_url",
        "brand_name",
        "sector",
        "end_date_text",
        "extraction_timestamp",
    ]
    _write_csv(campaigns_list, filepath, headers, append=False)


def save_product_incremental(product_dict, filepath):
    headers = [
        "product_url",
        "campaign_url",
        "product_name",
        "description",
        "original_price",
        "discount_price",
        "discount_percentage",
        "color",
        "sizes_status",
    ]
    _write_csv([product_dict], filepath, headers, append=True)


def _write_csv(data_list, filepath, headers, append=False):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    file_exists = os.path.isfile(filepath)
    mode = "a" if append else "w"

    with open(filepath, mode=mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")

        if not append or not file_exists or os.path.getsize(filepath) == 0:
            writer.writeheader()

        for item in data_list:
            writer.writerow(item)