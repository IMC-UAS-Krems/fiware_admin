import pandas as pd
import json
import os

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

print("\nTransforming playground data to FIWARE format:")
print("-> Opening raw data file...")
with open(os.path.join(CURR_DIR, 'spielplatz_wien_raw_data.json'), 'r', encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data['features'])


def transform_to_fiware(df):
    fiware_entities = []
    # spielplatz_details = {}
    for _, row in df.iterrows():
        feature = row
        entity_id = feature['id']
        entity_type = 'Playground'

        # Geometry
        coordinates = feature['geometry']['coordinates']
        location = {
            'type': 'geo:json',
            'value': {
                'type': 'Point',
                'coordinates': coordinates
            }
        }
        
        # Properies
        properties = feature['properties']
        name = properties["ANL_NAME"]
        type = properties["TYP_DETAIL"]
        details_text = properties["SPIELPLATZ_DETAIL"]
        details = [detail.strip() for detail in details_text.split(",") if detail.strip()]
        details = list(set(details))
        details.sort()
        
        # Build entity
        entity = {
            'id': entity_id,
            'type': entity_type,
            'location': location,
            'properties': {
                'name': {'type': 'Text', 'value': name},
                'type': {'type': 'Text', 'value': type},
                'details': {'type': 'Text', 'value': ", ".join(details)},
                # Add more properties as needed
            }
        }
        

        # for detail in row["properties"]["SPIELPLATZ_DETAIL"].split(","):
        #     detail = detail.strip()
        #     if not detail:
        #         continue
        #     if detail not in spielplatz_details:
        #         spielplatz_details[detail] = 1
        #     else:
        #         spielplatz_details[detail] += 1
                
        

    # print("\nPlayground details:")
    # for detail, count in spielplatz_details.items():
    #     print(f"{detail}: {count}")
        
transform_to_fiware(df)