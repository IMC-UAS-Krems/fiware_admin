import pandas as pd
import requests
import json
import os
import re
import sys
import unicodedata
import datetime

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

print("\nTransforming waste collection data from Wien to FIWARE format:")
print("-> Opening raw data file...")
with open(os.path.join(CURR_DIR, 'waste_collection_wien_raw_data.json'), 'r', encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data['features'])

fractionMapDe = {
    'FRAKTION_PA': 'Altpapier',
    'FRAKTION_BI': 'Biomüll',
    'FRAKTION_DO': 'Leichtverpackungen',
    'FRAKTION_G': 'Altglas',
    'FRAKTION_KV': 'Restmüll'
}
fractionMapEn = {
    'FRAKTION_PA': 'Paper',
    'FRAKTION_BI': 'Organic waste',
    'FRAKTION_DO': 'Lightweight packaging',
    'FRAKTION_G': 'Glass',
    'FRAKTION_KV': 'Residual waste'
}


def transform_to_fiware(df):
    fiware_entities = []
    for _, row in df.iterrows():
        feature = row
        entity_id = feature['id']
        entity_type = 'WasteCollectionPoint'

        # Geometry
        coordinates = feature['geometry']['coordinates']
        location = {
            'type': 'geo:json',
            'value': {
                'type': 'Point',
                'coordinates': coordinates
            }
        }

        # Properties
        properties = feature['properties']
        list_of_fraction_names = []
        for property in ['FRAKTION_PA', 'FRAKTION_BI', 'FRAKTION_DO', 'FRAKTION_G', 'FRAKTION_KV']:
            if properties[property]:
                list_of_fraction_names.append(fractionMapEn[property])

        # Handle FRAKTION
        fraktion = {
            'PA': {'type': 'Boolean', 'value': bool(properties['FRAKTION_PA'])},
            'BI': {'type': 'Boolean', 'value': bool(properties['FRAKTION_BI'])},
            'DO': {'type': 'Boolean', 'value': bool(properties['FRAKTION_DO'])},
            'G': {'type': 'Boolean', 'value': bool(properties['FRAKTION_G'])},
            'KV': {'type': 'Boolean', 'value': bool(properties['FRAKTION_KV'])},
            'TEXT': {'type': 'Text', 'value': ", ".join(sorted(list_of_fraction_names))},
        }

        # Other properties
        other_properties = {
            'BEZIRK': {'type': 'Number', 'value': properties['BEZIRK']},
            'STRASSE': {'type': 'Text', 'value': properties['STRASSE']},
            'BEZUG': {'type': 'Text', 'value': properties['BEZUG']},
            'ONR': {'type': 'Text', 'value': properties['ONR']},
            'URL_TEXT': {'type': 'URL', 'value': properties['URL_TEXT']}
        }

        entity = {
            'id': entity_id,
            'type': entity_type,
            'location': location,
            **fraktion,
            **other_properties
        }
        fiware_entities.append(entity)
    return fiware_entities


print("-> Transforming data to FIWARE format...")
fiware_data = transform_to_fiware(df)

print("-> Saving transformed data to JSON file...")
with open(CURR_DIR + "/" + 'waste_collection_wien_fiware.json', 'w', encoding="utf-8") as f:
    json.dump(fiware_data, f, indent=4, ensure_ascii=False)
print("DONE.\n")
