import csv
import ast
from collections import defaultdict

def merge_csv_records_by_name(input_csv_path, output_csv_path=None, merge_key='name'):
    """
    Merge records from a CSV file that have the same 'name' attribute.

    For records with the same name:
    - List values are appended (no duplicates)
    - String values are appended with newlines (no duplicate lines)
    - Other values are kept from the last occurrence

    Args:
        input_csv_path (str): Path to the input CSV file
        output_csv_path (str, optional): Path to save the merged CSV. If None, returns the merged data.
        merge_key (str): Column name to merge on (default 'name')

    Returns:
        If output_csv_path is None, returns a list of dictionaries with the merged records.
        Otherwise, saves to CSV and returns None.
    """
    merged_records = defaultdict(dict)

    # Read the CSV file
    with open(input_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames

        for row in reader:
            key = row.get(merge_key)
            if not key:
                continue

            for field, raw_value in row.items():
                if field == merge_key:
                    merged_records[key][merge_key] = key
                    continue

                if not raw_value:
                    continue

                # Try to parse list-literals
                value = raw_value
                try:
                    if raw_value.startswith('[') and raw_value.endswith(']'):
                        value = ast.literal_eval(raw_value)
                except (ValueError, SyntaxError):
                    value = raw_value

                # Merge into existing record
                if field in merged_records[key]:
                    existing = merged_records[key][field]

                    # Both lists → extend with only new items
                    if isinstance(existing, list) and isinstance(value, list):
                        to_add = [v for v in value if v not in existing]
                        existing.extend(to_add)

                    # Existing list, new single item → append if not present
                    elif isinstance(existing, list):
                        if value not in existing:
                            existing.append(value)

                    # New list, existing single item → build unique list
                    elif isinstance(value, list):
                        base = [existing]
                        to_add = [v for v in value if v != existing]
                        merged_records[key][field] = base + to_add

                    # Both strings → append as new line only if not already a line
                    else:
                        lines = existing.split('\n')
                        if value not in lines:
                            merged_records[key][field] = existing + '\n' + value

                else:
                    # First time seeing this field for this key
                    merged_records[key][field] = value

    result = list(merged_records.values())

    if output_csv_path:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result)
        return None

    return result