# --- MULTIPOLYGON SOLUTION ---
import pandas as pd
import json
import os
import geopandas
from shapely.geometry import shape, mapping

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

print("\nTransforming wind potential data to FIWARE format:")
print("-> Opening raw data file...")
with open(os.path.join(CURR_DIR, 'wind_potential_wien_raw_data.json'), 'r', encoding="utf-8") as f:
    data = json.load(f)

print("-> Transforming data to FIWARE format...")

def transform_to_fiware(data):
    # Extract features and create a list of dictionaries
    features = data['features']
    records = []
    for feature in features:
        try:
            # Extract relevant attributes
            entity_id = feature["id"]
            geometry = feature["geometry"]
            properties = feature["properties"]

            # Append record to the list
            records.append({
                "id": entity_id,
                "geometry": geometry,
                "POT_CLASS": properties["POT_CLASS"],
                "POT_CLASS_TXT": properties["POT_CLASS_TXT"]
            })
        except Exception as e:
            print(f"Error processing feature: {e}")

    # Create GeoDataFrame
    gdf = geopandas.GeoDataFrame(records, geometry=[shape(record["geometry"]) for record in records], crs="EPSG:4326")

    # Dissolve polygons based on POT_CLASS
    dissolved = gdf.dissolve(by="POT_CLASS", as_index=False)

    # Convert dissolved GeoDataFrame to GeoJSON format
    fiware_entities = []
    potential_class_to_text_map = {
        1: "High wind energy potential - greater than 4 m/s",
        2: "Medium wind energy potential - 2,5-4 m/s",
        3: "Low wind energy potential - less than 2,5 m/s",
    }

    for _, row in dissolved.iterrows():
        entity_id = f"WindPotentialClass{row['POT_CLASS']}"
        entity_type = "WindPotential"

        # Geometry - use mapping() to convert Shapely geometry to GeoJSON
        geometry = row["geometry"]
        geojson = mapping(geometry)  # This handles MultiPolygon structure correctly

        location = {
            "type": "geo:json",
            "value": geojson,
        }
        
        entity = {
            "id": entity_id,
            "type": entity_type,
            "location": location,
            "windPotentialClass": {
                "type": "Number",
                "value": row["POT_CLASS"],
            },
            "windPotentialClassText": {
                "type": "Text",
                "value": potential_class_to_text_map.get(
                    row["POT_CLASS"], "Unknown"
                ),
            },
        }
        fiware_entities.append(entity)

    return fiware_entities

fiware_data = transform_to_fiware(data)

print("-> Saving transformed data to JSON file...")
with open(CURR_DIR + "/" + 'wind_potential_wien_fiware.json', 'w', encoding="utf-8") as f:
    json.dump(fiware_data, f, indent=4, ensure_ascii=False)
print("DONE.\n")

# --- SOLUTION FOR SEPARATE POLYGONS ---
# import pandas as pd
# import json
# import os

# CURR_DIR = os.path.dirname(os.path.abspath(__file__))

# print("\nTransforming wind potential data to FIWARE format:")
# print("-> Opening raw data file...")
# with open(os.path.join(CURR_DIR, 'wind_potential_wien_raw_data.json'), 'r', encoding="utf-8") as f:
#     data = json.load(f)
# df = pd.DataFrame(data['features'])
# print("-> Transforming data to FIWARE format...")


# def transform_to_fiware(df):
#     fiware_entitites = []
#     for _, row in df.iterrows():
#         feature = row
#         entity_id = feature["id"]
#         entity_type = "WindPotential"

#         # Geometry
#         coordinates = feature["geometry"]["coordinates"]
#         # In the dataset rings are store in an invalid format, they are for some reason nested one more layer deep
#         if isinstance(coordinates[0][0][0], list):
#             # Remove the extra layer of nesting
#             coordinates = coordinates[0]

#         location = {
#             "type": "geo:json",
#             "value": {
#                 "type": "Polygon",
#                 "coordinates": coordinates,
#             },
#         }

#         # Properties
#         properties = feature["properties"]

#         # Entity
#         potential_class_to_text_map = {
#             1: "High wind energy potential - greater than 4 m/s",
#             2: "Medium wind energy potential - 2,5-4 m/s",
#             3: "Low wind energy potential - less than 2,5 m/s",
#         }
#         entity = {
#             "id": entity_id,
#             "type": entity_type,
#             "location": location,
#             "windPotentialClass": {
#                 "type": "Number",
#                 "value": properties["POT_CLASS"],
#             },
#             "windPotentialClassText": {
#                 "type": "Text",
#                 "value": potential_class_to_text_map.get(
#                     properties["POT_CLASS"], "Unknown"
#                 ),
#             },
#         }

#         # Append to entities list
#         fiware_entitites.append(entity)
#     return fiware_entitites


# fiware_data = transform_to_fiware(df)

# print("-> Saving transformed data to JSON file...")
# with open(CURR_DIR + "/" + 'wind_potential_wien_fiware.json', 'w', encoding="utf-8") as f:
#     json.dump(fiware_data, f, indent=4, ensure_ascii=False)
# print("DONE.\n")
