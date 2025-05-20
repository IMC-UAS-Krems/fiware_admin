import requests
import os
import sys
import pandas as pd
import json
from shapely.geometry import shape
from shapely.geometry import Polygon
import numpy as np
import re
from shapely.geometry import Polygon
from datetime import datetime


# --- Setup paths ---
CURR_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURR_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# --- API configuration ---
BASE_URL = "https://gis.lfrz.gv.at/api/geodata/i009501/ogc/features/v1/collections"

def create_general_attribute(type, value):
    """Create a new attribute for the entity."""
    return {
        "type": type,
        "value": value,
        "metadata": {}
    }

def create_location(geometry):
    """Create location attribute based on geometry type."""
    if geometry["type"] == "Point":
        location = {
            "type": "geo:json",
            "value": {
                "type": "Point",
                "coordinates": [
                    geometry["coordinates"][0],
                    geometry["coordinates"][1]
                ]
            },
            "metadata": {}
        }
    elif geometry["type"] == "Polygon":
        coordinates = Polygon(geometry["coordinates"][0])
        centroid = coordinates.centroid
        location = {
            "type": "geo:json",
            "value": {
                "type": "Point",
                "coordinates": [
                    centroid.x,
                    centroid.y
                ]
            },
            "metadata": {}
        }
    else:
        raise ValueError("Unsupported geometry type")
    
    return location

def create_id(field_use, field_parcel_id, date, id_choice):
    """
        Create a unique id based on three choices gives as an argument from the user
        args:
            field_use: str
            date: Datetime object
            id_choice: int
            field_parcel_id: int
        returns:
            unique id
    """
    if id_choice == 1:
        id = f'LandParcel-{field_use}-{date}'
    elif id_choice == 2:
        id = f'LandParcel-{date}'
    else:
        id = f'LandParcel-{field_parcel_id}'

    return id

def translate_land_use(field_use):
    """Translate land use code to English."""
    field_use_dict = {
        "ACKERLAND": "farmland",
        "WEINGARTENFLÄCHEN IM ERTRAG INKL. JUNGANLAGEN UND SCHNITTWEINGÄRTEN": "wineyard",
        "GRÜNLAND": "grassland",
    }
    return field_use_dict.get(field_use)

def categorize_funding(funding):
    organisation_a = 0
    organisation_b = 0
    organisation_c = 0
    organisaton_d = 0
    oragnisation_e = 0
    if funding == 1693:
        organisation_a = 1
    elif funding == 1696:
        organisation_b = 1
    elif funding == 1742:
        organisation_c = 1
    elif funding == 1783:
        organisaton_d = 1
    elif funding == 1822:
        oragnisation_e = 1
    else:
        pass
    return organisation_a, organisation_b, organisation_c, organisaton_d, oragnisation_e

def categorize_land_use(field_use):
    if field_use == "farmland":
        use_1 = 1
        use_2 = 0
        use_3 = 0
    elif field_use == "wineyard":
        use_1 = 0
        use_2 = 1
        use_3 = 0
    elif field_use == "grassland":
        use_1 = 0
        use_2 = 0
        use_3 = 1
    else:
        use_1 = 0
        use_2 = 0
        use_3 = 0
    return use_1, use_2, use_3

def convert_to_fiware_entity(feature, id_choice):
    properties = feature["properties"] # Extract properties
    geometry = feature.get("geometry", {}) # Extract geometry

    # Attributes
    field_use  = translate_land_use(properties["fnar_bezeichnung"])
    if field_use is None:
        return None
    
    dateObserved = datetime.fromisoformat(properties["geom_date_created"]).replace(tzinfo=None).isoformat()
    parcel_id = properties["fs_kennung"]
    id = create_id(field_use, parcel_id, dateObserved, id_choice)
    location = create_location(geometry)
    organisation_a, organisation_b, organisation_c, organisation_d, organisation_e = categorize_funding(properties["fart_id"])
    use_1, use_2, use_3 = categorize_land_use(field_use)

    entity = {
        "id": id,
        "type": "LandParcel",
        "funding": create_general_attribute("Text", properties["fart_id"]),
        "field_parcel_id": create_general_attribute("Number",parcel_id),
        "dateObserved": create_general_attribute("DateTime", dateObserved),
        "location": location,
        "area": create_general_attribute("Number", int(properties["fs_flaeche_ha"]*100)),
        "length": create_general_attribute("Number", properties["gml_length"]),
        "oragnisation_a": create_general_attribute("Text", organisation_a),
        "organisation_b": create_general_attribute("Text", organisation_b),
        "organisation_c": create_general_attribute("Text", organisation_c),
        "organisation_d": create_general_attribute("Text", organisation_d),
        "organisation_e": create_general_attribute("Text", organisation_e),
        "farmland": create_general_attribute("Text", use_1),
        "wineyard": create_general_attribute("Text", use_2),
        "grassland": create_general_attribute("Text", use_3),
        "gml_id": create_general_attribute("Text", properties["gml_id"]),
        "measurand": {
            "type": "List",
            "value": [
                f"length, {properties['gml_length']}, GQ, Length",
                f"area, {properties['fs_flaeche_ha']}, GQ, Area",
            ],
            "metadata": {}
        }
    }

    return entity

def convert_to_fiware_json(id_choice):
    # Convert and save as FIWARE NGSI-v2
    fiware_entities = []

    # fetch all feldstuecke collections
    collections = []
    # Send a GET request to the API
    response = requests.get(BASE_URL)
    if response.status_code == 200:
        data = response.json()
        # Extract only feldstuecke collections from 2020 to 2024
        collections = [
            collection['id']
            for collection in data.get('collections', [])
            if 'feldstuecke' in collection.get('id', '')
            and re.search(r'202[0-4]', collection.get('id', ''))
        ]

    else:
        print(f"Failed to retrieve collections. Status code: {response.status_code}")

    for collection in collections:
        collection_url = f"{BASE_URL}/{collection}/items"
        response = requests.get(collection_url, params={"limit": 1000})
        features = response.json()

        if "features" in features:
            for feature in features["features"]:
                entity = convert_to_fiware_entity(feature, id_choice)
                if entity is None:
                    continue
                fiware_entities.append(entity)
        else:
            print(f"Error fetching features for collection {collection}: {features}")

    # Save FIWARE-compatible JSON
    fiware_path = os.path.join(DATA_DIR, 'fiware_data.json')
    with open(fiware_path, 'w', encoding='utf-8') as f:
        json.dump(fiware_entities, f, ensure_ascii=False, indent=2)

    print(f"Saved FIWARE-compatible entities to {fiware_path}")

if __name__ == "__main__":
    
    # Validate arguments given
    if not isinstance(sys.argv[1],int) or sys.argv[1] > 3 or len(sys.argv) < 2:
        print(f'Usage: python process_data.py <ID-Choice>')
        print("Please enter an integer between 1 and 3")
        print(f'Enter a number as one of your choices \n 1 to categorize data points by their land use \n 2 to categorize them all in one category \n 3 to visualize each point independently')
        sys.exit(1)

    id_choice = sys.argv[1]
    
    convert_to_fiware_json(id_choice)