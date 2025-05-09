import pandas as pd
import requests
import json
import os
import re
import sys
import unicodedata
import datetime

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

metadata = pd.read_csv(os.path.join(CURR_DIR, 'metadata.csv'))

DATA_DIR = os.path.join(CURR_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    
POLLUTANT_MAP = {
    1: "SO2",
    5: "NO",
    6: "NOx",
    7: "PM10",
    8: "NO2",
    9: "O3",
    10: "CO",
    6001: "PM2.5",
    38: "PM2.5",
}
    
POLLUTANT_DESCRIPTION  = {
    "SO2": "Sulfur Dioxide",
    "NO": "Nitrogen Monoxide",
    "NOx": "Nitrogen oxides",
    "PM10": "Particulate Matter 10μm",
    "NO2": "Nitrogen Dioxide",
    "O3": "Ozone",
    "CO": "Carbon Monoxide",
    "PM2.5": "Particulate Matter 2.5μm"
}

def download_files_and_merge_in_one_file(parquet_files, output_path, raw_dir):
    """
    Download parquet files from the given URLs and merge them into a single DataFrame with daily aggregation.
    """
    dataframes = []

    for url in parquet_files:
        file_name = url.split('/')[-1]
        local_path = os.path.join(raw_dir, file_name)

        if not os.path.exists(local_path):
            print(f"Downloading {file_name} from {url}")
            response = requests.get(url)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded {file_name}")
            else:
                print(f"Failed to download {file_name}")
                continue
        else:
            print(f"{file_name} already exists locally, skipping.")

        df = pd.read_parquet(local_path)
        dataframes.append(df)

    merged_df = pd.concat(dataframes, ignore_index=True)
    merged_df.drop(columns=[
        'End', 'AggType', 'Validity', 'Verification', 'ResultTime',
        'DataCapture', 'FkObservationLog'
    ], inplace=True, errors='ignore')

    merged_df['Unit'] = merged_df['Unit'].str.replace('ug.m-3', 'ug/m3')
    merged_df['Start'] = pd.to_datetime(merged_df['Start'])
    merged_df['Date'] = merged_df['Start'].dt.floor('d')
    merged_df['Samplingpoint'] = merged_df['Samplingpoint'].str.replace('AT/', '')

    metadata_df = clean_metadata(metadata)
    df = merged_df.merge(metadata_df, on='Samplingpoint', how='left')

    df['PollutantName'] = df['Pollutant'].map(POLLUTANT_MAP)
    df['PollutantName'] = df['PollutantName'].fillna('Pollutant_' + df['Pollutant'].astype(str))
    df['Pollutant'] = df["PollutantName"]

    df = df.groupby([
        'StationName', 'Date', 'Pollutant', 'Unit', 'Lon', 'Lat',
        'Municipality', 'StationArea', 'StationType'
    ], as_index=False).agg({'Value': 'mean'})

    df.to_parquet(output_path, index=False)
    
    print(f"Merged DataFrame saved to {output_path}")
    
    for url in parquet_files:
        file_name = url.split('/')[-1]
        local_path = os.path.join(raw_dir, file_name)
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"Deleted {file_name}")
  
def clean_metadata(met_df):
    met_df.rename(columns={
    'Sampling Point Id': 'Samplingpoint',
    'Air Quality Station Name': 'StationName',
    'Longitude': 'Lon',
    'Latitude': 'Lat',
    'Municipality': 'Municipality',
    'Air Quality Station Area': 'StationArea',
    'Air Quality Station Type': 'StationType'
    }, inplace=True)
    
    met_df = met_df[['Samplingpoint', 'StationName', 'Lon', 'Lat', 'Municipality', 'StationArea', 'StationType']]
    
    return met_df



def generate_entity_id(station_name: str, date: datetime) -> str:
    # remove umlauts/accents
    normalized = unicodedata.normalize("NFKD", station_name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-")

    date_str = date.strftime("%Y-%m-%dT%H:%M:%S")

    return f"AT-AirQualityObserved-{slug}-{date_str}"



def convert_to_fiware_json(df_path):
    
    
    df = pd.read_parquet(df_path)
    unique_station_names = []
    
    entities = []

    # Group by StationName + Date to aggregate pollutants across sampling points
    grouped = df.groupby([
        'StationName', 'Date', 'Lon', 'Lat', 'Municipality', 'StationArea'
    ])
    

    for (station_name, date, lon, lat, municipality, area), group in grouped:
        
        if not station_name in unique_station_names:
            unique_station_names.append(station_name)

        
        entity = {
            "id": generate_entity_id(station_name, date),
            "type": "AirQualityObserved",
            "dateObserved": {
                "type": "DateTime",
                "value": date.strftime('%Y-%m-%dT00:00:00Z'),
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
                    "coordinates": [round(lon, 6), round(lat, 6)]
                },
                "metadata": {}
            },
            "address": {
                "type": "PostalAddress",
                "value": {
                    "addressCountry": "AT",
                    "addressLocality": municipality,
                    "streetAddress": area
                },
                "metadata": {}
            },
            "dataProvider": {
                "type": "Text",
                "value": "AT_EnvironmentalAgency",
                "metadata": {}
            },
            "source": {
                "type": "URL",
                "value": "https://data.gv.at",
                "metadata": {}
            },
            "measurand": {
                "type": "List",
                "value": [],
                "metadata": {}
            }
        }

        for _, row in group.iterrows():
            pollutant = row['Pollutant']
            if pollutant not in POLLUTANT_DESCRIPTION:
                continue
            value = round(row['Value'], 2)
            entity[pollutant] = {
                "type": "Number",
                "value": value,
                "metadata": {}
            }
            measurand_str = f"{pollutant},{value},GQ,{POLLUTANT_DESCRIPTION[pollutant]}"
            entity["measurand"]["value"].append(measurand_str)

        entities.append(entity)
    
    print(f"Unique station names: {unique_station_names}")

    return entities

def fetch_parquet_links(city_name: str) -> pd.DataFrame:
    """
    Fetch parquet file download links for a given city from the API.
    Returns a DataFrame with a single column of URLs.
    """
    url = "https://eeadmz1-downloads-api-appservice.azurewebsites.net/ParquetFile/urls"
    payload = {
        "countries": ["AT"],
        "cities": [city_name],
        "pollutants": [],
        "dataset": 1,
        "aggregationType": None,
        "dateTimeStart": None,
        "dateTimeEnd": None,
        "email": None,
        "source": "Website"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/csv"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    from io import StringIO
    csv_text = response.text
    df = pd.read_csv(StringIO(csv_text), header=None, skiprows=1)
    
    urls = []
    
    for index, row in df.iterrows():
        url = row[0]
        urls.append(url)
    
    return urls


if __name__ == "__main__":
    allowed_cities = {"Graz", "Linz", "Innsbruck", "Wien", "Klagenfurt", "Salzburg"}

    if len(sys.argv) < 2:
        print('Usage: python script.py <CityName1> <CityName2> ...')
        print(f"Allowed cities: {', '.join(allowed_cities)}")
        sys.exit(1)

    city_names = sys.argv[1:]

    for city_name in city_names:
        if city_name not in allowed_cities:
            print(f"City '{city_name}' not recognized. Skipping. Choose from: {', '.join(allowed_cities)}")
            continue

        DATA_ROOT = os.path.join(CURR_DIR, 'data')
        CITY_DIR = os.path.join(DATA_ROOT, city_name)
        RAW_DIR = os.path.join(CITY_DIR, 'raw')
        os.makedirs(RAW_DIR, exist_ok=True)

        merged_file_path = os.path.join(CITY_DIR, 'merged_data.parquet')
        fiware_file_path = os.path.join(CITY_DIR, 'fiware_data.json')

        if os.path.exists(merged_file_path) and os.path.exists(fiware_file_path):
            print(f"Files for '{city_name}' already exist. Skipping download and processing.")
            continue

        parquet_files = fetch_parquet_links(city_name)

        if not os.path.exists(merged_file_path):
            download_files_and_merge_in_one_file(parquet_files, merged_file_path, RAW_DIR)

        entities = convert_to_fiware_json(merged_file_path)
        with open(fiware_file_path, 'w') as f:
            json.dump(entities, f, indent=4, ensure_ascii=False)

        print(f"Processing for '{city_name}' completed.\n")
