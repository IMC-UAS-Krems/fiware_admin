import pandas as pd
import numpy as np
from datetime import datetime, date
import re
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

# desired number of sites to simulate, if None, all sites from the sights file will be used
SITES_TO_SIMULATE = 8

START_DATE = datetime(2025, 6, 1)
END_DATE = datetime(2025, 6, 30)
FREQUENCY = "6H"  # how often to sample the data, eg "1H" for hourly, "4H" for every 4 hours or "30min" for every 30 minutes or "D" for daily
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
BASE_O3_PPB = 30.0
BASE_PM25_UG_M3 = 12.0
BASE_EVAPORATION_RATE = 0.006
YEARLY_AVG_TEMP = 10.75
YEARLY_AMPLITUDE_TEMP = 10
DAILY_AMPLITUDE_TEMP = 11.0
DAILY_AMPLITUDE_SEASONAL_SWING = 3.0

CORRELATED_NOISE_VARS = ['temp', 'humidity', 'co2', 'nox', 'o3', 'pm25']
CORRELATION_MATRIX = np.array([
    [1.0, -0.7, 0.3, 0.2, 0.6, 0.1],   # temperature vs. others
    [-0.7, 1.0, -0.2, -0.1, -0.5, 0.4],  # humidity vs. others
    [0.3, -0.2, 1.0, 0.5, 0.2, 0.3],   # co2 vs. others
    [0.2, -0.1, 0.5, 1.0, 0.1, 0.4],   # nox vs. others
    [0.6, -0.5, 0.2, 0.1, 1.0, 0.0],   # o3 vs. others
    [0.1, 0.4, 0.3, 0.4, 0.0, 1.0]    # pm25 vs. others
])
NOISE_STD_DEVS = [0.5, 4, 3, 1.5, 5, 2]

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
    "Toskanagarten": {"temp_offset": 2.0, "humidity_offset": -15.0, "light_multiplier": 1.3, "soil_evaporation_mod": 1.5, "co2_offset": 5, "nox_offset": 0, "o3_multiplier": 1.2, "pm25_offset": -2, "electricity_multiplier": 0.2},
    "Rosengarten": {"temp_offset": 1.0, "humidity_offset": -5.0, "light_multiplier": 1.25, "soil_evaporation_mod": 1.2, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.3, "pm25_offset": -1, "electricity_multiplier": 0.1},
    "Naturnaher Felsengarten": {"temp_offset": 2.5, "humidity_offset": -20.0, "light_multiplier": 1.4, "soil_evaporation_mod": 1.8, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.1, "pm25_offset": -1, "electricity_multiplier": 0.0},
    "Italienischer Schachbrettgarten": {"temp_offset": 0.5, "humidity_offset": -5.0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.1, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.4, "pm25_offset": -2, "electricity_multiplier": 0.0},
    "Winzergarten": {"temp_offset": 1.0, "humidity_offset": -5.0, "light_multiplier": 1.2, "soil_evaporation_mod": 1.3, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.1, "pm25_offset": -3, "electricity_multiplier": 0.0},
    "Weiden „Hotel“ mit Garten des Regenbogens": {"temp_offset": 0.5, "humidity_offset": 0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.0, "co2_offset": 5, "nox_offset": 0, "o3_multiplier": 1.3, "pm25_offset": -1, "electricity_multiplier": 0.3},
    "Weltgrößte Kräuterspirale": {"temp_offset": 1.5, "humidity_offset": -8.0, "light_multiplier": 1.3, "soil_evaporation_mod": 1.4, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.2, "pm25_offset": -1, "electricity_multiplier": 0.0},
    "Omas Gemüsegarten": {"temp_offset": 0.0, "humidity_offset": 0.0, "light_multiplier": 1.0, "soil_evaporation_mod": 1.0, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.2, "pm25_offset": -2, "electricity_multiplier": 0.05},


    # Shady, Wooded, or Water-Heavy Areas
    "Asia Garten nach Feng Shui (eingeschränkter Zugang mit Rollstuhl)": {"temp_offset": -1.0, "humidity_offset": 10.0, "light_multiplier": 0.7, "soil_evaporation_mod": 0.8, "co2_offset": -5, "nox_offset": 0, "o3_multiplier": 0.7, "pm25_offset": 0, "electricity_multiplier": 0.3},
    "Waldweg": {"temp_offset": -2.5, "humidity_offset": 15.0, "light_multiplier": 0.3, "soil_evaporation_mod": 0.6, "co2_offset": -15, "o3_multiplier": 0.4, "pm25_offset": -2, "nox_offset": 0, "electricity_multiplier": 0.1},
    "Biotop Teich erleben": {"temp_offset": -1.5, "humidity_offset": 20.0, "light_multiplier": 1.1, "soil_evaporation_mod": 0.5, "co2_offset": -5, "nox_offset": 0, "o3_multiplier": 0.6, "pm25_offset": -1, "electricity_multiplier": 2.0},
    "Gesundheitswassergarten": {"temp_offset": -0.5, "humidity_offset": 15.0, "light_multiplier": 1.0, "soil_evaporation_mod": 0.7, "co2_offset": 10, "nox_offset": 0, "o3_multiplier": 0.7, "pm25_offset": 1, "electricity_multiplier": 1.0},
    "Brunnengarten": {"temp_offset": -0.2, "humidity_offset": 10.0, "light_multiplier": 1.0, "soil_evaporation_mod": 0.9, "co2_offset": 5, "nox_offset": 0, "o3_multiplier": 0.8, "pm25_offset": 2, "electricity_multiplier": 0.4},


    # Buildings & High-Traffic Areas
    "Abenteuergarten": {"temp_offset": 1.0, "humidity_offset": -5.0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.2, "co2_offset": 30, "nox_offset": 1, "o3_multiplier": 0.8, "pm25_offset": 5, "electricity_multiplier": 1.5},
    "Gartenarena": {"temp_offset": 0.5, "humidity_offset": -5.0, "light_multiplier": 1.3, "soil_evaporation_mod": 1.1, "co2_offset": 50, "nox_offset": 2, "o3_multiplier": 0.7, "pm25_offset": 6, "electricity_multiplier": 6.0},
    "Gastgarten": {"temp_offset": 2.0, "humidity_offset": 0.0, "light_multiplier": 0.9, "soil_evaporation_mod": 1.0, "co2_offset": 40, "nox_offset": 5, "o3_multiplier": 0.6, "pm25_offset": 4, "electricity_multiplier": 8.0},
    "Thermohaus mit saisonalen Pflanzen-Spezialitäten": {"temp_offset": 8.0, "humidity_offset": 25.0, "light_multiplier": 0.9, "soil_evaporation_mod": 0.4, "co2_offset": 15, "nox_offset": 1, "o3_multiplier": 0.7, "pm25_offset": 2, "electricity_multiplier": 4.0},
    "Tierischer Bauerngarten": {"temp_offset": 0.5, "humidity_offset": 5.0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.1, "co2_offset": 35, "nox_offset": 2, "o3_multiplier": 0.7, "pm25_offset": 5, "electricity_multiplier": 0.7},
    "Haus der Sonne mit Himmelszelt und Garten.Bistro": {"temp_offset": 1.5, "humidity_offset": -5.0, "light_multiplier": 1.0, "soil_evaporation_mod": 1.0, "co2_offset": 35, "nox_offset": 4, "o3_multiplier": 0.7, "pm25_offset": 4, "electricity_multiplier": 7.0},


    # Other Specific Gardens
    "Wellnessgarten": {"temp_offset": 0.0, "humidity_offset": 5.0, "light_multiplier": 0.9, "soil_evaporation_mod": 0.8, "co2_offset": 5, "nox_offset": 0, "o3_multiplier": 1.0, "pm25_offset": 2, "electricity_multiplier": 1.2},
    "Portugiesischer Feuerkunst Garten": {"temp_offset": 1.0, "humidity_offset": -10.0, "light_multiplier": 1.2, "soil_evaporation_mod": 1.3, "co2_offset": 5, "nox_offset": 3, "o3_multiplier": 0.8, "pm25_offset": 2, "electricity_multiplier": 0.5},
    "Garten der Ästhetik": {"temp_offset": 0.0, "humidity_offset": 0, "light_multiplier": 1.1, "soil_evaporation_mod": 1.0, "co2_offset": 2, "nox_offset": 0, "o3_multiplier": 1.5, "pm25_offset": -3, "electricity_multiplier": 0.1},
    "Garten der Sehnsucht": {"temp_offset": 0.2, "humidity_offset": 5.0, "light_multiplier": 0.95, "soil_evaporation_mod": 0.9, "co2_offset": 5, "nox_offset": 0, "o3_multiplier": 1.4, "pm25_offset": 1, "electricity_multiplier": 0.1},

    # Default profile
    "Default Garden": {"temp_offset": 0.0, "humidity_offset": 0.0, "light_multiplier": 1.0, "soil_evaporation_mod": 1.0, "co2_offset": 0, "nox_offset": 0, "o3_multiplier": 1.0, "pm25_offset": 0, "electricity_multiplier": 0.1},
}

# ==============================================================================
# DATA SIMULATION
# ==============================================================================


class SensorModel:
    
    @staticmethod
    def generate_correlated_noise(num_samples, correlation_matrix, std_devs):
        """
        Generates correlated noise for multiple variables.
        - correlation_matrix: A matrix defining the correlation between variables.
        - std_devs: A list of standard deviations for each variable noise
        """
        if len(correlation_matrix) != len(std_devs):
            raise ValueError(
                "Correlation matrix and standard deviations must have the same dimension.")

        independent_noise = np.random.normal(
            0, 1, size=(len(std_devs), num_samples))

        # apply Cholesky decomposition to introduce correlation
        c = np.linalg.cholesky(correlation_matrix)
        correlated_noise = np.dot(c, independent_noise)

        scaled_noise = (correlated_noise.T * np.array(std_devs)).T
        return scaled_noise
        
    @staticmethod
    def generate_temperature(time_df, noise: np.ndarray) -> np.ndarray:
        """
        Generates a temperature time series with a smooth seasonal cycle
        and more realistic, multi-layered noise for hourly data.
        """
        # The offset is set to 120 to shift the peak summer heat to late July
        seasonal_cycle = YEARLY_AMPLITUDE_TEMP * np.sin(2 * np.pi * (time_df['day_of_year'] - 120) / 365.25)

        daily_amplitude = DAILY_AMPLITUDE_TEMP + DAILY_AMPLITUDE_SEASONAL_SWING * np.sin(2 * np.pi * (time_df['day_of_year'] - 120) / 365.25)

        diurnal_cycle = daily_amplitude / 2 * np.sin(2 * np.pi * (time_df['hour_of_day'] - 10) / 24)


        return YEARLY_AVG_TEMP + seasonal_cycle + diurnal_cycle + noise
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
    def generate_humidity(temp_series, season_params, noise):
        """
        Generates a humidity time series based on temperature and seasonal parameters.
        """
        # Model humidity as inversely correlated to temperature, starting from a seasonal average, eg: high humidity in winter, lower in summer.
        humidity_series = season_params['avg_humidity'] - \
            (temp_series * 1.2) + np.random.normal(0, 4, len(temp_series))
        # add outliers to simulate real-world variability
        humidity_series += np.random.choice(
            [0, 5, -5, 10, -10], size=len(temp_series), p=[0.7, 0.1, 0.1, 0.05, 0.05]) + noise
        # ensure the humidity values stay in a realistic range
        return humidity_series.clip(25, 98)

    @staticmethod
    def generate_soil_moisture(temp_series, season_params) -> np.ndarray:
        """
        Generates soil moisture with a stateful rain model for more realistic weather patterns.
        """
        moisture = np.zeros(len(temp_series))
        moisture[0] = 85.0

        prob_rain_starts = season_params['rain_chance'] / 12.0
        prob_rain_continues = 0.85 

        is_raining = False
        for i in range(1, len(temp_series)):
            if is_raining:
                if np.random.rand() > prob_rain_continues:
                    is_raining = False
            else:
                if np.random.rand() < prob_rain_starts:
                    is_raining = True

            temp = temp_series.iloc[i]
            evaporation_multiplier = 1 + (max(0, temp) / 15)**2
            current_moisture = moisture[i-1] - \
                (BASE_EVAPORATION_RATE * evaporation_multiplier)

            # --- apply Rain ---
            if is_raining:
                current_moisture += np.random.uniform(5, 10)

            current_moisture += np.random.normal(0, 0.2)
            moisture[i] = np.clip(current_moisture, 15, 98)

        return moisture

    @staticmethod
    def generate_electricity(time_df, opening_hour, closing_hour) -> pd.Series:
        """
        Generates electricity usage correlated with both time of day and season.
        """
        def get_daily_usage(hour):
            if not (opening_hour <= hour < closing_hour):
                return np.random.uniform(5, 10)  # Low base usage overnight
            elif hour == opening_hour or hour == closing_hour - 1:
                return np.random.uniform(20, 30)
            else:
                return np.random.uniform(40, 60)  # Peak hours

        # peaks in late July
        seasonal_multiplier = 1 + 0.4 * \
            np.sin(2 * np.pi * (time_df['day_of_year'] - 120) / 365.25)

        daily_base = time_df['hour_of_day'].apply(get_daily_usage)
        seasonally_adjusted = daily_base * seasonal_multiplier

        outlier_mask = np.random.rand(len(time_df)) < 0.005
        seasonally_adjusted[outlier_mask] = np.random.uniform(70, 110)

        return seasonally_adjusted

    @staticmethod
    def generate_o3(temp_series, light_series, noise) -> np.ndarray:
        """Generates an O3 time series, correlated with temperature and light."""
        temp_effect = (temp_series - YEARLY_AVG_TEMP) * 1.5
        light_effect = (light_series / 100) * 15
        o3_series = BASE_O3_PPB + temp_effect + light_effect + noise
        return o3_series.clip(lower=5)

    @staticmethod
    def generate_pm25(humidity_series, noise) -> np.ndarray:
        """Generates a PM2.5 time series, inversely correlated with humidity."""
        humidity_effect = (80 - humidity_series) * 0.1
        pm25_series = BASE_PM25_UG_M3 + humidity_effect + noise
        return pm25_series.clip(lower=3)
    
    @staticmethod
    def generate_co2_nox(base_co2, base_nox, noise_co2, noise_nox):
        return base_co2 + noise_co2, base_nox + noise_nox

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
                'longitude': sight['location']['value']['coordinates'][0],
                'latitude': sight['location']['value']['coordinates'][1]
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
        """Generates baseline environmental patterns, now using pre-generated correlated noise."""

        num_samples = len(self.base_df)
        correlated_noise = SensorModel.generate_correlated_noise(
            num_samples, CORRELATION_MATRIX, NOISE_STD_DEVS)

        noise_df = pd.DataFrame(correlated_noise.T, columns=[
                                f"{var}_noise" for var in CORRELATED_NOISE_VARS])

        self.base_df['base_temp'] = SensorModel.generate_temperature(
            self.base_df, noise_df['temp_noise'].values)
        self.base_df['base_co2'], self.base_df['base_nox'] = SensorModel.generate_co2_nox(
            BASE_CO2_PPM, BASE_NOX_PPB, noise_df['co2_noise'].values, noise_df['nox_noise'].values
        )

        all_seasonal_data = []
        for season, params in SEASONAL_PARAMETERS.items():
            season_mask = (self.base_df['season'] == season)
            time_subset = self.base_df[season_mask].copy()
            if time_subset.empty:
                continue

            noise_subset = noise_df[season_mask]
            time_subset['base_humidity'] = SensorModel.generate_humidity(
                time_subset['base_temp'], params, noise_subset['humidity_noise'].values)
            time_subset['base_light'] = SensorModel.generate_light(
                time_subset, params)  # Light noise remains independent
            time_subset['base_soil_moisture'] = SensorModel.generate_soil_moisture(
                time_subset['base_temp'], params)
            all_seasonal_data.append(time_subset)

        self.base_df = pd.concat(all_seasonal_data).sort_index()

        self.base_df['base_o3'] = SensorModel.generate_o3(
            self.base_df['base_temp'], self.base_df['base_light'], noise_df['o3_noise'].values)
        self.base_df['base_pm25'] = SensorModel.generate_pm25(
            self.base_df['base_humidity'], noise_df['pm25_noise'].values)

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
            station_data['o3'] = (station_data['base_o3']
                                  * modifiers.get('o3_multiplier', 1)).clip(0)
            station_data['pm25'] = (
                station_data['base_pm25'] + modifiers.get('pm25_offset', 0)).clip(0)
            base_electricity = SensorModel.generate_electricity(
                station_data, OPENING_HOUR, CLOSING_HOUR
            )
            station_data['electricity_kwh'] = (
                base_electricity * modifiers.get('electricity_multiplier', 1)).clip(0)

            # convert to FIWARE JSON format
            fiware_json_for_station = convert_df_to_fiware_json(station_data)
            total_entities_generated += len(fiware_json_for_station)

            # unique filename
            station_name = station['station_name'].replace(
                " ", "_").replace("/", "_")
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
        station_name_str = row['station_name']
        normalized = unicodedata.normalize("NFKD", station_name_str)
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).lower().strip("-")

        date_obj = row['timestamp']
        date_str = date_obj.strftime("%Y-%m-%dT%H:%M:%S")

        entity_id = f"AT-kittenberger-{slug}-{date_str}"

        entity = {
            "id": entity_id, "type": "SmartGardenSensor",
            "dateObserved": {"type": "DateTime", "value": row['timestamp'].isoformat() + "Z"},
            "stationId": {"type": "Text", "value": row['station_id']},
            "zoneName": {"type": "Text", "value": row['station_name']},
            "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [round(row['longitude'], 5), round(row['latitude'], 5)]}},
            "temperature": {"type": "Number", "value": int(round(row['temperature'], 0))},
            "relativeHumidity": {"type": "Number", "value": round(row['humidity'], 2)},
            "lightIntensity": {"type": "Number", "value": round(row['light_intensity'], 2)},
            "soilMoisture": {"type": "Number", "value": round(row['soil_moisture'], 2)},
            "co2": {"type": "Number", "value": round(row['co2'], 2)},
            "nox": {"type": "Number", "value": round(row['nox'], 2)},
            "o3": {"type": "Number", "value": round(row['o3'], 2)},
            "pm25": {"type": "Number", "value": round(row['pm25'], 2)},
            "electricityConsumption": {"type": "Number", "value": round(row['electricity_kwh'], 2)}
        }
        fiware_entities.append(entity)
    return fiware_entities

# ==============================================================================
# MAIN
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
