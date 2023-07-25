import argparse
import json
from client import FiwareClient
from random_helper import generate_simple_time_series, time_series_to_json

## Helper functions
def get_type(args):
    """
    Returns the entity type if given.
    """
    type = None
    if args.type is not None:
        type = args.type
    return type

def check_if_file_exists(path):
    """
    Checks if a given path exists
    """
    try:
        f = open(path)
    except FileNotFoundError:
        return False
    f.close()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='General Fiware admin util for Dataskop/Smart Communities projects.',
                                     epilog='Author: Ruben Ruiz-Torrubiano (ruben.ruiz@fh-krems.ac.at)')
    

    # BEGIN PARSING ARGUMENTS
    # Config file
    parser.add_argument('-c', '--config', metavar='<config_file>', nargs=1, 
                        help='Path to config file')
    
    # Fetch all entities
    parser.add_argument('-f', '--fetch',
                        action='store_true', 
                        help='Fetches all entities of a given type (all entities if no type specified).')
    
    # Specify entity type
    parser.add_argument('-t', '--type',
                        help='Specifies the type of the entity to be fetched or modified.')
    
    # Delete all entities
    parser.add_argument('-d', '--delete',
                        action='store_true',
                        help='Delete all the entities of the given type (all entities if no type given)')
    
    # Upload data from JSON file
    parser.add_argument('-u', '--upload', metavar='<json_data_file>',
                        help='Path to JSON file with data to upload. The data should be given as a JSON array of entities with IDs and attributes.')
    
    # Specify the Fiware-Service path
    parser.add_argument('-s', '--service', metavar='<service_path>',
                        help='Name of the Fiware-service path.')
    
    # Generate random data
    parser.add_argument('-g', '--generate',
                        action='store_true',
                        help='Generates random data.')
    
    # Minimum/Maximum range (use with -G)
    parser.add_argument('-m', '--min', type=int, default=0,
                        help='Minimum value for random data (default 0)')

    # Minimum/Maximum range (use with -G)
    parser.add_argument('-M', '--max', type=int, default=100,
                        help='Maximum value for random data (default 100)')
    
    # Number of data points to generate
    parser.add_argument('-b', '--batch-size', type=int, default=100,
                        help='Number of data points to generate for random data')

    args = parser.parse_args()
    # END PARSING ARGUMENTS
    
    try:
        with open(args.config[0]) as config_file:
            config_json = json.load(config_file)
            config = config_json["config"]
            service = ""
            if args.service:
                service = args.service
            client = FiwareClient(config["endpoint"], config["token"], service)

            if args.fetch:
                # Fetch entities
                print('Fetching all entities...')
                type = get_type(args)
                result = client.get_all_entities(type=type)
                print(result)
            if args.delete:
                # Delete entities
                print('Deleting entities...')
                type = get_type(args)
                result = client.delete_all_entities(type=type)
                print(result)
            if args.upload:
                # Upload data
                if check_if_file_exists(args.upload) is False:
                    print(f'Error: data file {args.upload} does not exist')
                    exit(1)
                with open(args.upload) as data_file:
                    data_json = json.load(data_file)
                    result = client.upload_entities(data_json)
                    print(result)
            if args.generate:
                # Generate random data
                type = get_type(args)
                data = generate_simple_time_series(args.min, args.max, args.batch_size, type_name=type)
                print('----------- Generated measurements -----------\n')
                print(data)
                data_json = time_series_to_json(data)
                result = client.upload_entities(data_json)
                print(result)

    except FileNotFoundError:
        print('Error: Config file could not be loaded')
        exit(1)