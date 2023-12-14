import requests
import logging
import base64
import os
import json

class DHIS2Connector:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

    def process_patient_files(self, directory='patients_to_sync'):
        files = sorted(os.listdir(directory), key=lambda x: os.path.getctime(os.path.join(directory, x)))
        for filename in files:
            if not filename.endswith('.json'):
                continue
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                patient_data = json.load(file)
            tracked_entity_data = patient_data.pop('trackedEntityType', None)
            if tracked_entity_data:
                response = self.make_api_call('trackedEntityInstances', method='POST', data=tracked_entity_data)
                if response and 'response' in response and 'importSummaries' in response['response']:
                    entity_id = response['response']['importSummaries'][0]['reference']
                    for enrollment in patient_data.get('enrollments', []):
                        for event in enrollment.get('events', []):
                            event['trackedEntityInstance'] = entity_id
                            self.make_api_call('events', method='POST', data=event)
                    new_filename = f"{entity_id}_{filename}"
                    os.rename(file_path, os.path.join(directory, new_filename))
                    user_input = input("Continue processing the next file? (yes/no): ").strip().lower()
                    if user_input != 'yes':
                        break

    def get_auth_header(self):
        """Create the authorization header for DHIS2 API requests."""
        credentials = f"{self.username}:{self.password}"
        credentials_bytes = credentials.encode('ascii')
        base64_bytes = base64.b64encode(credentials_bytes)
        base64_credentials = base64_bytes.decode('ascii')
        return {"Authorization": f"Basic {base64_credentials}"}

    def make_api_call(self, endpoint, method='GET', data=None):
        """Make an API call to the DHIS2 instance."""
        url = f"{self.base_url}/{endpoint}"
        headers = self.get_auth_header()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            # Add other HTTP methods as needed
            response.raise_for_status()
            return response.json()
        except requests.RequestException as err:
            logging.error(f"Error in DHIS2 API call: {err}")
            raise

