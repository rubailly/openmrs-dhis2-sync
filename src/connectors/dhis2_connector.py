import requests
import base64
import logging
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
            # Assuming that patient_data is a dictionary that contains the full tracked entity instance data
            # under a key that is not just 'trackedEntityType'. We need to find the correct key or construct
            # the full JSON object if necessary. For this example, let's assume the full data is under the key
            # 'trackedEntityInstance'.
            try:
                logging.info(f"Posting tracked entity instance data: {json.dumps(patient_data, indent=4)}")
                org_unit = patient_data.get('orgUnit')
                
                response = self.make_api_call('trackedEntityInstances', method='POST', data=patient_data)
                if response and 'response' in response and 'importSummaries' in response['response']:
                    entity_id = response['response']['importSummaries'][0]['reference']
                    for enrollment in patient_data.get('enrollments', []):
                        # Extract program, enrollmentDate, and incidentDate from each enrollment
                        program = enrollment.get('program')
                        enrollment_date = enrollment.get('enrollmentDate')
                        incident_date = enrollment.get('incidentDate')
                        for event in enrollment.get('events', []):
                            # Include program, orgUnit, enrollmentDate, and incidentDate in each event
                            event['program'] = program
                            event['orgUnit'] = org_unit  # orgUnit is still taken from the root level
                            event['enrollmentDate'] = enrollment_date
                            event['incidentDate'] = incident_date
                            event['trackedEntityInstance'] = entity_id
                            event['status'] = 'COMPLETED'  # Mark the event as completed
                            logging.info(f"Posting event data: {json.dumps(event, indent=4)}")
                            self.make_api_call('events', method='POST', data=event)
                    new_filename = f"{entity_id}_{filename}"
                    os.rename(file_path, os.path.join(directory, new_filename))
            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")
                continue

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

