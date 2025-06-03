import pandas as pd
import json
import os
import re

CURR_DIR = os.path.dirname(os.path.abspath(__file__))

print("\nTransforming kindergarten data to FIWARE format:")
print("-> Opening raw data file...")
with open(os.path.join(CURR_DIR, 'kindergarten_wien_raw_data.json'), 'r', encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data['features'])
# print(df.head())

# --- Preprocessing: Filter by TYP_TXT value counts ---
print("-> Preprocessing: Filtering by TYP_TXT value counts...")
# Extract the 'TYP_TXT' series
typ_txt_series = df['properties'].apply(lambda x: x.get('TYP_TXT'))

# Calculate value counts
typ_txt_counts = typ_txt_series.value_counts()

# Identify types that occur more than 15 times
valid_types = typ_txt_counts[typ_txt_counts > 15].index.tolist()

# Filter the DataFrame
df_filtered = df[df['properties'].apply(lambda x: x.get(
    # Use .copy() to avoid SettingWithCopyWarning
    'TYP_TXT') in valid_types)].copy()
print(f"-> Original number of features: {len(df)}")
print(
    f"-> Number of features after filtering by TYP_TXT counts (>15): {len(df_filtered)}")
print("-> Number of unique TYP_TXT values after filtering:", len(valid_types))
# --- End of Preprocessing ---


def clean_fiware_string(text_value):
    if text_value is None or not isinstance(text_value, str):
        return text_value  # Return as is if None or not a string

    # Characters explicitly forbidden by FIWARE documentation
    forbidden_chars = ['<', '>', '"', "'", '=', ';', '(', ')']
    for char in forbidden_chars:
        # Remove forbidden characters
        text_value = text_value.replace(char, '')

    # Replace multiple spaces with a single space and strip leading/trailing spaces
    text_value = ' '.join(text_value.split()).strip()

    return text_value


def transform_to_fiware(df):
    fiware_entities = []
    for _, row in df.iterrows():
        feature = row
        entity_id = feature['id']
        entity_type = 'Kindergarten'

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

        capacity_columns = [
            "FAMILIE_0_6", "FAMILIE_3_10",
            "HEILPAED_HORT_6_10", "HEILPAED_KDG_3_6",
            "HORT_6_10", "INTEGRAT_FAMILIE_0_6",
            "INTEGRAT_FAMILIE_3_10", "INTEGRAT_HORT_6_10",
            "INTEGRAT_KDG_3_6", "INTEGRAT_KLEINKINDER_0_3",
            "KDG_3_6", "HALBTAGS_KDG_3_6",
            "KLEINKINDER_0_3"
        ]

        total_capacity = 0
        for column in capacity_columns:
            if pd.notna(properties[column]) and properties[column] is not None:
                total_capacity += properties[column]

        kindergarten_type = clean_fiware_string(
            properties["TYP_TXT"].replace("<br>", " "))
        operator = clean_fiware_string(properties["BETREIBER"])
        name = clean_fiware_string(properties["BEZEICHNUNG"])
        adress = clean_fiware_string(properties["ADRESSE"])
        availability = "Private" if properties["TXTATT1"] == "Privat" else "Public"
        # URLs might need specific URL encoding if they contain special chars
        weblink = properties["WEBLINK1"]
        contact = clean_fiware_string(properties["KONTAKT"])

        entity = {
            'id': entity_id,
            'type': entity_type,
            'location': location,
            'capacity': {'type': 'Number', 'value': total_capacity},
            'kindergarten_type': {'type': 'Text', 'value': kindergarten_type},
            'operator': {'type': 'Text', 'value': operator},
            'name': {'type': 'Text', 'value': name},
            'address': {'type': 'Text', 'value': adress},
            'availability': {'type': 'Text', 'value': availability},
            'weblink': {'type': 'URL', 'value': weblink},
            'contact': {'type': 'Text', 'value': contact}
        }

        fiware_entities.append(entity)
    return fiware_entities


print("-> Transforming data to FIWARE format...")
fiware_data = transform_to_fiware(df_filtered)

print("-> Saving transformed data to file...")
with open(os.path.join(CURR_DIR, 'kindergarten_wien_fiware.json'), 'w', encoding='utf-8') as f:
    json.dump(fiware_data, f, ensure_ascii=False, indent=4)
print("DONE.\n")
