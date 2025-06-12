import pandas as pd
import numpy as np
from datetime import datetime
import json
import unicodedata
import logging
import os


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SITES_TO_SIMULATE = 5 # desired number of sites to simulate, if None, all sites from the sights file will be used

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 6, 10)
FREQUENCY = "12H" # how often to sample the data, eg "1H" for hourly, "4H" for every 4 hours or "30min" for every 30 minutes or "D" for daily
OPENING_HOUR = 9
CLOSING_HOUR = 18

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
SIGHTS_DATA_FILENAME = os.path.join(CUR_DIR, "kb_sights_map_fiware.json")
OUTPUT_DIR = os.path.join(CUR_DIR, "data")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Baseline
BASE_CO2_PPM = 415.0
BASE_NOX_PPB = 15.0
BASE_EVAPORATION_RATE = 0.006

SEASONAL_PARAMETERS = {
    # avg_temp: Average temperature in Celsius
    # temp_amplitude: Seasonal temperature amplitude in Celsius
    # avg_humidity: Average relative humidity in percentage
    # daylight_hours: Average daylight hours per day
    # rain_chance: Chance of rain as percentage (0.0 to 1.0)
    "winter": {
        "avg_temp": 1.0,
        "temp_amplitude": 8.0,
        "avg_humidity": 80.0,
        "daylight_hours": 9.0,
        "rain_chance": 0.35,
    },
    "spring": {
        "avg_temp": 10.0,
        "temp_amplitude": 12.0,
        "avg_humidity": 65.0,
        "daylight_hours": 13.0,
        "rain_chance": 0.40,
    },
    "summer": {
        "avg_temp": 21.0,
        "temp_amplitude": 14.0,
        "avg_humidity": 64.0,
        "daylight_hours": 15.5,
        "rain_chance": 0.42,
    },
    "autumn": {
        "avg_temp": 11.0,
        "temp_amplitude": 10.0,
        "avg_humidity": 75.0,
        "daylight_hours": 11.0,
        "rain_chance": 0.30,
    }
}


GARDEN_ZONE_CHARACTERISTICS = {
    # Open, Sunny, and Themed Gardens
    "Toskanagarten": {"temp_offset": 2.0, "humidity_offset": -15.0, "light_multiplier": 1.3, "soil_evaporation_mod": 1.5, "co2_offset": 5, "nox_offset": 0, "electricity_multiplier": 0.2},
    "Rosengarten": {"temp_offset": 1.0, "humidity_offset": -5.0, "light_multiplier": 1.25, "soil_evaporation_mod": 1.2, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.1},
    "Naturnaher Felsengarten": {"temp_offset": 2.5, "humidity_offset": -20.0, "light_multiplier": 1.4, "soil_evaporation_mod": 1.8, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.0},
    "Italienischer Schachbrettgarten": {"temp_offset": 0.5, "humidity_offset": -5.0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.1, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.0},
    "Winzergarten": {"temp_offset": 1.0, "humidity_offset": -5.0, "light_multiplier": 1.2, "soil_evaporation_mod": 1.3, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.0},
    "Weiden „Hotel“ mit Garten des Regenbogens": {"temp_offset": 0.5, "humidity_offset": 0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.0, "co2_offset": 5, "nox_offset": 0, "electricity_multiplier": 0.3},
    "Weltgrößte Kräuterspirale": {"temp_offset": 1.5, "humidity_offset": -8.0, "light_multiplier": 1.3, "soil_evaporation_mod": 1.4, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.0},
    "Omas Gemüsegarten": {"temp_offset": 0.0, "humidity_offset": 0.0, "light_multiplier": 1.0, "soil_evaporation_mod": 1.0, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.05},


    # Shady, Wooded, or Water-Heavy Areas
    "Asia Garten nach Feng Shui (eingeschränkter Zugang mit Rollstuhl)": {"temp_offset": -1.0, "humidity_offset": 10.0, "light_multiplier": 0.7, "soil_evaporation_mod": 0.8, "co2_offset": -5, "nox_offset": 0, "electricity_multiplier": 0.3},
    "Waldweg": {"temp_offset": -2.5, "humidity_offset": 15.0, "light_multiplier": 0.3, "soil_evaporation_mod": 0.6, "co2_offset": -15, "nox_offset": 0, "electricity_multiplier": 0.1},
    "Biotop Teich erleben": {"temp_offset": -1.5, "humidity_offset": 20.0, "light_multiplier": 1.1, "soil_evaporation_mod": 0.5, "co2_offset": -5, "nox_offset": 0, "electricity_multiplier": 2.0},
    "Gesundheitswassergarten": {"temp_offset": -0.5, "humidity_offset": 15.0, "light_multiplier": 1.0, "soil_evaporation_mod": 0.7, "co2_offset": 10, "nox_offset": 0, "electricity_multiplier": 1.0},
    "Brunnengarten": {"temp_offset": -0.2, "humidity_offset": 10.0, "light_multiplier": 1.0, "soil_evaporation_mod": 0.9, "co2_offset": 5, "nox_offset": 0, "electricity_multiplier": 0.4},


    # Buildings & High-Traffic Areas
    "Abenteuergarten": {"temp_offset": 1.0, "humidity_offset": -5.0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.2, "co2_offset": 30, "nox_offset": 1, "electricity_multiplier": 1.5},
    "Gartenarena": {"temp_offset": 0.5, "humidity_offset": -5.0, "light_multiplier": 1.3, "soil_evaporation_mod": 1.1, "co2_offset": 50, "nox_offset": 2, "electricity_multiplier": 6.0},
    "Gastgarten": {"temp_offset": 2.0, "humidity_offset": 0.0, "light_multiplier": 0.9, "soil_evaporation_mod": 1.0, "co2_offset": 40, "nox_offset": 5, "electricity_multiplier": 8.0},
    "Thermohaus mit saisonalen Pflanzen-Spezialitäten": {"temp_offset": 8.0, "humidity_offset": 25.0, "light_multiplier": 0.9, "soil_evaporation_mod": 0.4, "co2_offset": 15, "nox_offset": 1, "electricity_multiplier": 4.0},
    "Tierischer Bauerngarten": {"temp_offset": 0.5, "humidity_offset": 5.0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.1, "co2_offset": 35, "nox_offset": 2, "electricity_multiplier": 0.7},
    "Haus der Sonne mit Himmelszelt und Garten.Bistro": {"temp_offset": 1.5, "humidity_offset": -5.0, "light_multiplier": 1.0, "soil_evaporation_mod": 1.0, "co2_offset": 35, "nox_offset": 4, "electricity_multiplier": 7.0},


    # Other Specific Gardens
    "Wellnessgarten": {"temp_offset": 0.0, "humidity_offset": 5.0, "light_multiplier": 0.9, "soil_evaporation_mod": 0.8, "co2_offset": 5, "nox_offset": 0, "electricity_multiplier": 1.2},
    "Portugiesischer Feuerkunst Garten": {"temp_offset": 1.0, "humidity_offset": -10.0, "light_multiplier": 1.2, "soil_evaporation_mod": 1.3, "co2_offset": 5, "nox_offset": 3, "electricity_multiplier": 0.5},
    "Garten der Ästhetik": {"temp_offset": 0.0, "humidity_offset": 0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.0, "co2_offset": 2, "nox_offset": 0, "electricity_multiplier": 0.1},
    "Garten der Sehnsucht": {"temp_offset": 0.2, "humidity_offset": 5.0, "light_multiplier": 0.95, "soil_evaporation_mod": 0.9, "co2_offset": 5, "nox_offset": 0, "electricity_multiplier": 0.1},

    # Default profile
    "Default Garden": {"temp_offset": 0.0, "humidity_offset": 0.0, "light_multiplier": 1.0, "soil_evaporation_mod": 1.0, "co2_offset": 0, "nox_offset": 0, "electricity_multiplier": 0.1},
}

# ==============================================================================
# DATA SIMULATION
# ==============================================================================


class SensorModel:
    @staticmethod
    def generate_temperature(time_df, season_params) -> np.ndarray:
        """
        Generates a temperature time series based on seasonal parameters as well as diurnal cycle. Add a spice of noise to simulate real-world variability.
        """
        # simulats the yearly temperature cycle
        seasonal_cycle = season_params['temp_amplitude'] / 2 * \
            np.sin(2 * np.pi * (time_df['day_of_year'] - 90) / 365.25)
        # simulate the daily temperature change (warmer afternoons, colder nights)
        diurnal_cycle = season_params['temp_amplitude'] / 2 * \
            np.sin(2 * np.pi * (time_df['hour_of_day'] - 10) / 24)
        # noise: random minor noise to simulate real-world variability
        noise = np.random.normal(0, 0.5, size=len(time_df))
        return season_params['avg_temp'] + seasonal_cycle + diurnal_cycle + noise

    @staticmethod
    def generate_light(time_df, season_params) -> np.ndarray:
        """
        Generates a light intensity time series based on seasonal parameters and diurnal cycle.
        """
        # get the average number of daylight hours for the current season.
        daylight_hours = season_params['daylight_hours']
        # scale the daily cycle to fit the seasonal light period
        scaled_hour = (time_df['hour_of_day'] - (12 -
                       daylight_hours / 2)) * (24 / daylight_hours)
        # generate the daily light curve using a sine wave on the scaled hours
        diurnal_light = 100 * np.sin(2 * np.pi * scaled_hour / 24)

        light_series = diurnal_light + np.random.normal(0, 5, len(time_df))
        # ensure light intensity is non-negative
        return light_series.clip(lower=0)

    @staticmethod
    def generate_humidity(temp_series, season_params):
        """
        Generates a humidity time series based on temperature and seasonal parameters.
        """
        # Model humidity as inversely correlated to temperature, starting from a seasonal average, eg: high humidity in winter, lower in summer.
        humidity_series = season_params['avg_humidity'] - \
            (temp_series * 1.2) + np.random.normal(0, 4, len(temp_series))
        # add outliers to simulate real-world variability
        humidity_series += np.random.choice(
            [0, 5, -5, 10, -10], size=len(temp_series), p=[0.7, 0.1, 0.1, 0.05, 0.05])
        # ensure the humidity values stay in a realistic range
        return humidity_series.clip(25, 98)

    @staticmethod
    def generate_soil_moisture(temp_series, season_params) -> np.ndarray:
        moisture = np.zeros(len(temp_series))
        moisture[0] = 85.0

        # convert the daily probability of rain into an hourly chance
        hourly_rain_chance = season_params['rain_chance'] / 24.0

        for i in range(1, len(temp_series)):
            # make evaporation faster when the temperature is higher
            evaporation_mod = 1 + max(0, temp_series.iloc[i]) / 20
            # aply the continuous drying effect from evaporation
            moisture[i] = moisture[i-1] - \
                (BASE_EVAPORATION_RATE * evaporation_mod)
            if np.random.rand() < hourly_rain_chance:
                moisture[i] += np.random.uniform(20, 40)
            # add some random noise to simulate real-world variability
            moisture[i] += np.random.normal(0, 2)
        # ennsure the moisture values stay in a realistic range
        return np.clip(moisture, 15, 95)

    @staticmethod
    def generate_electricity(opening_hour, closing_hour) -> callable:
        """
        Generates a function that simulates electricity usage in the garden based on the hour of the day.
        """
        profile = {h: np.random.uniform(5, 8)
                   for h in range(24)}
        # simulate higher usage during opening hours
        profile.update({h: np.random.uniform(20, 30)
                       for h in range(opening_hour-1, opening_hour+1)})
        # simulate peak usage during business hours
        profile.update({h: np.random.uniform(40, 60)
                       for h in range(opening_hour+1, closing_hour-1)})
        # set medium usage as the garden is closin
        profile.update({h: np.random.uniform(15, 25)
                       for h in range(closing_hour-1, closing_hour+1)})
        # add some out-of-hours usage for maintenance
        profile.update({h: np.random.uniform(5, 10)
                       for h in range(0, opening_hour-1)})
        # add some outliers
        for h in range(24):
            if np.random.rand() < 0.05:
                profile[h] = np.random.uniform(100, 200)
        # return a function that can look up the usage for any given hour
        return lambda hour: profile.get(hour, 5)

# ==============================================================================
# DATA GENERATOR
# ==============================================================================


class DataGenerator:
    def __init__(self, sights_file):
        """Initializes the generator by preparing the sensor stations and simulation timeline."""
        self.stations_df = self.initialize_stations_from_file(sights_file)
        self.base_df = self.create_simulation_timeline()

    def initialize_stations_from_file(self, filename):
        """
        Creates a df of sensor stations from the provided json file.
        """
        with open(filename, 'r', encoding='utf-8') as f:
            sights_data = json.load(f)

        stations_list = []
        for sight in sights_data:
            # Filter out admin points
            if "Kasse" in sight["name"]["value"] or "Büro" in sight["name"]["value"]:
                continue

            stations_list.append({
                'station_id': sight['id'],
                'station_name': sight['name']['value'],
                'latitude': sight['location']['value']['coordinates'][0],
                'longitude': sight['location']['value']['coordinates'][1]
            })
    
        all_stations = pd.DataFrame(stations_list)

        # ENsure number of sites desired is matched
        if SITES_TO_SIMULATE is not None and SITES_TO_SIMULATE < len(all_stations):
            logging.info(
                f"Randomly selecting {SITES_TO_SIMULATE} stations from {len(all_stations)} available sights.")
            final_stations = all_stations.sample(
                n=SITES_TO_SIMULATE)
        else:
            logging.info(
                f"Using all {len(all_stations)} available sights as sensor stations.")
            final_stations = all_stations

        return final_stations

    def create_simulation_timeline(self):
        """
        Builds the master timeline with timestamps and derived time features.
        """
        timestamps = pd.to_datetime(pd.date_range(
            start=START_DATE, end=END_DATE, freq=FREQUENCY))
        df = pd.DataFrame({'timestamp': timestamps})
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['month'] = df['timestamp'].dt.month
        df['season'] = df['month'].apply(lambda m: "winter" if m in [12, 1, 2] else "spring" if m in [
                                         3, 4, 5] else "summer" if m in [6, 7, 8] else "autumn")
        logging.info(
            f"Time foundation created with {len(df)} data points per station.")
        return df

    def generate_base_patterns(self):
        """Generates baseline environmental patterns for the entire timeline using seasonal parameters."""
        logging.info(
            "Generating baseline environmental patterns using seasonal data...")
        all_seasonal_data = []
        for season, params in SEASONAL_PARAMETERS.items():
            season_mask = (self.base_df['season'] == season)
            time_subset = self.base_df[season_mask].copy()
            if time_subset.empty:
                continue

            temp_series = SensorModel.generate_temperature(time_subset, params)
            time_subset['base_temp'] = temp_series
            time_subset['base_humidity'] = SensorModel.generate_humidity(
                temp_series, params)
            time_subset['base_light'] = SensorModel.generate_light(
                time_subset, params)
            time_subset['base_soil_moisture'] = SensorModel.generate_soil_moisture(
                time_subset['base_temp'], params)
            all_seasonal_data.append(time_subset)

        self.base_df = pd.concat(all_seasonal_data).sort_index()

        # Generate non seasonal base data
        self.base_df['base_co2'] = BASE_CO2_PPM + \
            np.random.normal(0, 3, len(self.base_df))
        self.base_df['base_nox'] = BASE_NOX_PPB + \
            np.random.normal(0, 1.5, len(self.base_df))
        electricity_profile_func = SensorModel.generate_electricity(
            OPENING_HOUR, CLOSING_HOUR)
        self.base_df['base_electricity'] = self.base_df['hour_of_day'].apply(
            electricity_profile_func)

    # In DataGenerator class
    def generate_and_save_data_per_station(self):
        """
        Applies modifiers for each site and saves its data to a separate FIWARE json file
        """
        logging.info(
            "Applying zone characteristics and generating final dataset for each station...")

        total_entities_generated = 0

        # Loop through each station defined in the stations_df
        for _, station in self.stations_df.iterrows():
            station_data = self.base_df.copy()
            station_data['station_id'] = station['station_id']
            station_data['station_name'] = station['station_name']
            station_data['latitude'] = station['latitude']
            station_data['longitude'] = station['longitude']

            # Find the best matching characteristic profile key to apply modifiers
            best_match_key = "Default Garden"
            for key in GARDEN_ZONE_CHARACTERISTICS.keys():
                if key in station['station_name']:
                    best_match_key = key
                    break

            modifiers = GARDEN_ZONE_CHARACTERISTICS[best_match_key]

            # Apply modifiers to generate the final sensor values
            station_data['temperature'] = station_data['base_temp'] + \
                modifiers.get('temp_offset', 0)
            station_data['humidity'] = (
                station_data['base_humidity'] + modifiers.get('humidity_offset', 0)).clip(10, 100)
            station_data['light_intensity'] = (
                station_data['base_light'] * modifiers.get('light_multiplier', 1)).clip(0)
            station_data['soil_moisture'] = (station_data['base_soil_moisture'] * (
                1 / modifiers.get('soil_evaporation_mod', 1))).clip(0, 100)
            station_data['co2'] = station_data['base_co2'] + \
                modifiers.get('co2_offset', 0)
            station_data['nox'] = station_data['base_nox'] + \
                modifiers.get('nox_offset', 0)
            station_data['electricity_kwh'] = (
                station_data['base_electricity'] * modifiers.get('electricity_multiplier', 1)).clip(0)

            # convert to FIWARE JSON format
            fiware_json_for_station = convert_df_to_fiware_json(station_data)
            total_entities_generated += len(fiware_json_for_station)

            # unique filename
            station_name = station['station_name'].replace(" ", "_").replace("/", "_")
            station_name = unicodedata.normalize(
                'NFKD', station_name).encode('ascii', 'ignore').decode('ascii')
            station_name = station_name.lower()
            station_output_filename = f"{station_name}.json"
            output_path = os.path.join(OUTPUT_DIR, station_output_filename)

            # Save the JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(fiware_json_for_station, f,
                          ensure_ascii=False, indent=2)

            logging.info(
                f"  -> Saved data for station '{station['station_id']}' to '{output_path}'")

        return total_entities_generated

    def run(self):
        """Executes the full simulation pipeline and returns the total number of entities generated."""
        self.generate_base_patterns()
        total_entities = self.generate_and_save_data_per_station()
        return total_entities


# ==============================================================================
# Convert to FIWARE JSON
# ==============================================================================


def convert_df_to_fiware_json(df: pd.DataFrame):
    """Converts a DataFrame of sensor readings into a list of FIWARE NGSI-LD entities."""
    logging.info(
        f"Converting {len(df)} records to FIWARE NGSI-LD JSON format...")
    fiware_entities = []
    for _, row in df.iterrows():
        # create a unique ID for each entity
        entity_id = f"urn:ngsi-ld:SmartGardenSensor:{row['station_id']}:{row['timestamp'].strftime('%Y%m%dT%H%M%S')}"

        entity = {
            "id": entity_id, "type": "SmartGardenSensor",
            "dateObserved": {"type": "DateTime", "value": row['timestamp'].isoformat() + "Z"},
            "stationId": {"type": "Text", "value": row['station_id']},
            "zoneName": {"type": "Text", "value": row['station_name']},
            "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [round(row['longitude'], 5), round(row['latitude'], 5)]}},
            "temperature": {"type": "Number", "value": round(row['temperature'], 2)},
            "relativeHumidity": {"type": "Number", "value": round(row['humidity'], 2)},
            "lightIntensity": {"type": "Number", "value": round(row['light_intensity'], 2)},
            "soilMoisture": {"type": "Number", "value": round(row['soil_moisture'], 2)},
            "co2": {"type": "Number", "value": round(row['co2'], 2)},
            "nox": {"type": "Number", "value": round(row['nox'], 2)},
            "electricityConsumption": {"type": "Number", "value": round(row['electricity_kwh'], 2)}
        }
        fiware_entities.append(entity)
    return fiware_entities

# ==============================================================================
#MAIN
# ==============================================================================


def main():
    """
    Main function to run the simulation and save the output.
    """
    generator = DataGenerator(sights_file=SIGHTS_DATA_FILENAME)

    total_entities = generator.run()

    logging.info(
        f"Simulation complete. All files saved in '{OUTPUT_DIR}' directory.\n")
    logging.info(
        f"Total entities generated across all files: {total_entities}\n")



if __name__ == "__main__":
    main()
