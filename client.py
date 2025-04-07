# Implementation of the necessary parts of the Fiware NGSI v2 API
# Specs: https://fiware-ges.github.io/orion/api/v2/stable/

from dataclasses import dataclass
import requests
import json
from datetime import datetime
from dateutil import parser

@dataclass
class MeasurementRequest():
    urn: str
    name: str

@dataclass
class MeasurementResult():
    urn: str
    name: str
    value: str
    timestamp: datetime

class FiwareClient():
    """
    Class that implements the Fiware NGSI v2 API.
    """
    def __init__(self, endpoint, token, service=None) -> None:
        """
        Constructor accepts two parameters:
        @param endpoint: URL of API endpoint.
        @param token: access token.
        @param service: service path.
        """
        self.endpoint = endpoint
        self.token = token
        self.service = service
        
    def send_get(self, request):
        """
        Helper method that sends a GET request with the authorization token
        """
        return requests.get(request, headers = {"X-Auth-Token": self.token, "fiware-service": self.service})
    
    def send_post(self, request, body):
        """
        Helper method that sends a POST request with the authorization token
        """
        return requests.post(request, headers = {"X-Auth-Token": self.token, "fiware-service": self.service}, json = body)

    def get_all_entities(self, type=None):
        """
        Gets all entities of a given type (if type provided)
        """
        call_endpoint = f"{self.endpoint}/entities?"
        if type is not None:
            call_endpoint += "type=" + type + "&limit=1000&offset="
        else:
            call_endpoint += "limit=1000&offset="
        offset = 0
        call_endpoint_base = call_endpoint
        final_response = []
        while True:
            call_endpoint = call_endpoint_base + str(offset)
            response = self.send_get(call_endpoint)
            response_json = response.json()
            if len(response_json) == 0:
                break
            for value in response_json:
                final_response.append(value)
            offset += 1000
        return final_response
    
    def delete_all_entities(self, type=None):
        """
        Gets all entities of a given type (if type provided)
        """
        call_endpoint = f"{self.endpoint}/op/update"
        # First query all entities to get their IDs
        result = self.get_all_entities(type)
        ids = []
        for entity in result:
            ids.append(
                {
                    "id": entity["id"]
                })
        payload = {
            "actionType": "delete",
            "entities": ids
        }
        print(payload)
        response = self.send_post(call_endpoint, body = payload)
        return response
    
    def query_entity(self, measurement_request: MeasurementRequest):
        """
        Queries latest data for an entity.
        @param urn: the unique identifier for the entity.
        """
        call_endpoint = f"{self.endpoint}/entities/{measurement_request.urn}"
        response = self.send_get(call_endpoint)

        response_json = response.json()
        result = None
        #print(json.dumps(response_json, indent=4, sort_keys=True))
        if measurement_request.name in response_json:
            ts = None
            if "TimeInstant" in response_json:
                ts_str = response_json["TimeInstant"]["value"]
                ts = parser.parse(ts_str)
            result = MeasurementResult(measurement_request.urn, measurement_request.name, response_json[measurement_request.name]["value"], ts)

        return result
    
    def upload_entities(self, entities, key_values = False):
        """
        Uploads entities to the Fiware instance.
        """
        call_endpoint = f"{self.endpoint}/op/update"
        if key_values:
            call_endpoint += "?options=keyValues"
        
        payload = {
            "actionType": "append_strict",
            "entities": entities
        }
        response = self.send_post(call_endpoint, body = payload)
        if response.status_code >= 400:
            print(f"Error: {response.text}")
            print(f"Response code: {response.status_code}")
        return response
    
    def get_payload_size_bytes(self, entities):
        """
        Returns the total size of the payload with entities in bytes.
        """
        
        payload = {
            "actionType": "append_strict",
            "entities": entities
        }
        
        payload_json = json.dumps(payload)
        return len(payload_json.encode("utf-8"))
        
    def upload_entities_with_size_check(self, entities, key_values = False, max_size_bytes = 1024 * 1024):
        """
        Uploads entities to the Fiware instance with a size check.
        Returns an error if entities exceed the max size.
    
        Args:
            entities: List of entities to upload
            key_values: Whether to use keyValues option
            max_size_bytes: Maximum size in bytes (default: 1MB)
        """
        payload_size = self.get_payload_size_bytes(entities)
        if payload_size > max_size_bytes:
            print(f"Error: Payload size ({payload_size/1024:.2f} KB) exceeds maximum ({max_size_bytes/1024:.2f} KB)")
            return {"error": "Payload too large", "size_kb": payload_size/1024}
        
        # Use the original upload_entities method
        return self.upload_entities(entities, key_values)
        
    def batch_and_upload_entities(self, entities, key_values=False, max_batch_size_bytes=1024*1024):
        """
        Splits entities into batches and uploads each batch.
        
        Args:
            entities: List of entities to upload
            key_values: Whether to use keyValues option
            max_batch_size_bytes: Maximum batch size in bytes (default: 1MB, must be lower then fiware maximum)
        
        Returns:
            List of responses from each batch upload
        """
        batch = []
        current_batch_size_bytes = 0
        batch_number = 0
        responses = []
        
        print(f"Total entities to upload: {len(entities)}")
        
        for entity in entities:
            # Calculate the new batch size if we add this entity
            test_batch = batch + [entity]
            new_batch_size = self.get_payload_size_bytes(test_batch)
            
            if new_batch_size > max_batch_size_bytes and batch:
                print(f"Uploading batch {batch_number + 1} with {len(batch)} entities ({current_batch_size_bytes/1024:.2f} KB)")
                response = self.upload_entities(batch, key_values)
                responses.append(response)
                
                # Reset for next batch
                batch = [entity]
                current_batch_size_bytes = self.get_payload_size_bytes(batch)
                batch_number += 1
            else:
                batch.append(entity)
                current_batch_size_bytes = new_batch_size
        
        # send last entities
        if batch:
            print(f"Uploading final batch {batch_number + 1} with {len(batch)} entities ({current_batch_size_bytes/1024:.2f} KB)")
            response = self.upload_entities(batch, key_values)
            responses.append(response)
        
        return responses