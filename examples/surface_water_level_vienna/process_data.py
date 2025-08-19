import requests
import json
from bs4 import BeautifulSoup
import sys
from datetime import datetime
import os
import re
from pyproj import Transformer

def extract_start_date(filename):
    try:
        date_str = filename.split('_')[0]
        return datetime.strptime(date_str, '%Y-%m-%d')
    except Exception:
        return None

transformer = Transformer.from_crs("EPSG:31256", "EPSG:4326", always_xy=True)

def parse_geometry(geometry_str):
    match = re.match(r'POINT\s*\(\s*([-\d\.]+)\s+([-\d\.]+)\s*\)', geometry_str)
    if match:
        x, y = match.groups()
        x, y = float(x), float(y)
        lon, lat = transformer.transform(x, y)
        return [lon, lat]
    else:
        return [0.0, 0.0]

def transform_to_fiware(entry):
    fiware_entries = []
    station_id = entry.get("ID", "Unknown")
    station_name = entry.get("Name", "Unknown")
    location_coords = parse_geometry(entry.get("Lage", {}).get("Geometrie", "POINT (0 0)"))
    address = {
        "addressCountry": "AT",
        "addressLocality": entry.get("Lage", {}).get("Ort", ""),
        "streetAddress": entry.get("Lage", {}).get("Adresse", "")
    }

    data_provider = "AT_EnvironmentalAgency"
    source_url = "https://data.gv.at"

    for param in entry.get("Messparameter", []):
        if param.get("Parameter") != "Pegel":
            continue
        unit = param.get("Einheit", "cm")
        for measurement in param.get("Messwerte", []):
            timestamp = measurement.get("Datum")
            value = measurement.get("Wert")
            if timestamp is None or value is None:
                continue
            fiware_entry = {
                "id": f"AT-WaterLevelObserved-{station_id}-{timestamp}",
                "type": "WaterLevelObserved",
                "dateObserved": {
                    "type": "DateTime",
                    "value": timestamp,
                    "metadata": {}
                },
                "stationName": {
                    "type": "Text",
                    "value": station_name,
                    "metadata": {}
                },
                "location": {
                    "type": "geo:json",
                    "value": {
                        "type": "Point",
                        "coordinates": location_coords
                    },
                    "metadata": {}
                },
                "address": {
                    "type": "PostalAddress",
                    "value": address,
                    "metadata": {}
                },
                "dataProvider": {
                    "type": "Text",
                    "value": data_provider,
                    "metadata": {}
                },
                "source": {
                    "type": "URL",
                    "value": source_url,
                    "metadata": {}
                },
                "waterLevel": {
                    "type": "Number",
                    "value": value,
                    "metadata": {
                        "unit": {
                            "type": "Text",
                            "value": unit
                        }
                    }
                }
            }
            fiware_entries.append(fiware_entry)
    return fiware_entries

def main(from_date_str, to_date_str):
    base_url = 'https://stp.wien.gv.at/smartdata.wien/gis/ma45exports/ow/W819R5/'

    from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
    to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

    response = requests.get(base_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    json_files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.json')]

    selected_files = []
    for filename in json_files:
        file_date = extract_start_date(filename)
        if file_date and from_date <= file_date <= to_date:
            selected_files.append(filename)

    if not selected_files:
        print("No files found in the given date range.")
        return

    all_fiware_data = []

    for filename in selected_files:
        file_url = base_url + filename
        file_response = requests.get(file_url)
        file_response.raise_for_status()
        data = file_response.json()
        if isinstance(data, list):
            for entry in data:
                fiware_entries = transform_to_fiware(entry)
                all_fiware_data.extend(fiware_entries)
        elif isinstance(data, dict):
            fiware_entries = transform_to_fiware(data)
            all_fiware_data.extend(fiware_entries)
        else:
            print(f"Unexpected data format in file: {filename}")

    output_dir = os.path.join('data', f"{from_date_str}_to_{to_date_str}")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = os.path.join(output_dir, 'fiware_data.json')
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_fiware_data, f, ensure_ascii=False, indent=4)

    print(f"FIWARE data saved to '{output_filename}'")

if __name__ == '__main__':
    if len(sys.argv) == 2:
        from_date_arg = sys.argv[1]
        to_date_arg = datetime.now().strftime('%Y-%m-%d')
    elif len(sys.argv) == 3:
        from_date_arg = sys.argv[1]
        to_date_arg = sys.argv[2]
    else:
        print("Usage: python usecase2.py <from_date> [to_date]")
        print("Example 1 (range): python usecase2.py 2022-08-01 2022-08-31")
        print("Example 2 (until today): python usecase2.py 2022-08-01")
        sys.exit(1)

    main(from_date_arg, to_date_arg)