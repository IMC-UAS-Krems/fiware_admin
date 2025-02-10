import numpy as np
import pandas as pd
from numpy import random as rn
import random
import string

def generate_random_id(size):
    """
    Generates a random id where the random part is of the given size
    """
    random_string = ''.join(random.choice(string.hexdigits) for i in range(size))
    return 'id-' + random_string


def generate_simple_time_series(min, max, size, interval=1, type_name="DefaultType"):
    """
    Generates a time series using uniform random numbers between [min, max], 
    and assigns each measurement a timestamp and a random id.
    The timestamp is calculated to get the last 'size' measurements in intervals of 'interval' seconds.
    For instance, if size=100 and interval=2s, the first timestamp starts at the current timestamp (now)
    minus 200 seconds. 

    @min: minimum value for time series.
    @max: maximum value for time series.
    @size: number of samples to generate.
    @interval: the measurement interval (in seconds). Default: 1 s.
    """
    cols = {'id': [],  'type': [], 'dateObserved': [], 'measurement': []}
    df = pd.DataFrame(data = cols)

    sample = rn.uniform(min, max, size)
    df['measurement'] = sample
    ids = np.ones((size, ), dtype=int)
    
    vfunc = np.vectorize(generate_random_id)
    df['id'] = vfunc(ids*16)

    df['dateObserved'] = pd.Timestamp.utcnow() - pd.Series(pd.Timedelta(seconds=(size*interval - i*interval)) for i in range(size))

    df['type'] = type_name

    return df

def row_to_json(row):
    """
    Converts a row of a dataframe of a generated dataset into its corresponding JSON object.
    """
    json_obj = {"id": row[0], 
                "type": row[1],
                "dateObserved": {
                    "type": "DateTime",
                    "value": row[2].isoformat().replace('+00:00', 'Z'),
                    "metadata": {}
                },
                "measurement": {
                    "type": "Number",
                    "value": row[3],
                    "metadata": {}
                }}
    return json_obj


def time_series_to_json(df):
    """
    Helper function to convert a generated time series into a JSON object with
    the expected format by NGSIv2.
    """
    result = df.apply(row_to_json, axis=1).to_list()
    return result


def add_metadata(data_json, metadata):
    """
    Adds the metadata contained in the variable metadata to all the elements in the current
    dataset.
    """
    for entity in data_json:
        for key, value in metadata.items():
            entity[key] = value

