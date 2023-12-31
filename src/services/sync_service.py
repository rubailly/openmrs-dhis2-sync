import json
import os
import logging
from connectors.openmrs_connector import OpenMRSConnector
from connectors.dhis2_connector import DHIS2Connector
from models.dhis2_models import DHIS2TrackedEntity, DHIS2DataElement
from models.openmrs_models import OpenMRSPatient, OpenMRSObservation
from config.mappings import load_mappings
from utils.progress_tracker import ProgressTracker

class SyncService:
    def __init__(self, openmrs_config, dhis2_config, progress_tracker_file):
        self.openmrs_connector = OpenMRSConnector(**openmrs_config)
        self.dhis2_connector = DHIS2Connector(**dhis2_config)
        self.mappings = {}  # Initialize the mappings attribute
        self.progress_tracker = ProgressTracker(progress_tracker_file)

    def load_form_mappings(self, form_id):
        """Load mappings for a specific form and return them."""
        mapping_file = f'mappings/forms/form_{form_id}_mappings.json'
        if os.path.exists(mapping_file):
            return load_mappings(mapping_file)
        logging.error(f"Mapping file not found for form ID {form_id}")
        return None

    def process_patient_and_encounters(self, patient_id, encounter_ids, location_id):
        """Process a patient and their encounters, transforming them into a DHIS2-compliant JSON object ready for submission to DHIS2."""
        logging.info(f"Processing patient ID: {patient_id}")
        # Load attribute mappings
        attribute_mappings = load_mappings('mappings/attribute_mappings.json')
        # Load location, province and district mappings
        location_mappings = load_mappings('mappings/location_mappings.json')
        province_mappings = load_mappings('mappings/province_mappings.json')
        district_mappings = load_mappings('mappings/district_mappings.json')
        # Initialize the DHIS2-compliant JSON object
        # Use the location ID provided by the user to get the org unit ID
        org_unit_id = location_mappings.get(location_id)
        if not org_unit_id:
            logging.error(f"Location ID {location_id} not found in the mappings. Please provide a valid location ID.")
            raise ValueError(f"Location ID {location_id} not found in the mappings.")
        dhis2_compliant_json = {
            "trackedEntityType": "j9TllKXZ3jb",
            "orgUnit": org_unit_id,
            "attributes": [],
            "enrollments": []
        }
        try:
            # Fetch patient data
            patient_data = self.openmrs_connector.fetch_patient_data(patient_id)
            # Transform patient data to DHIS2 attributes format
            for openmrs_attr, dhis2_attr in attribute_mappings.items():
                # Get the patient attribute value from patient_data using the OpenMRS attribute name
                patient_attribute_value = patient_data.get(openmrs_attr)
                # Special handling for gender to convert 'F' to 'Female' and 'M' to 'Male'
                # and for 'Citizenship' or 'country' to set its value to 'D6Us3GQryHU'
                if openmrs_attr == 'Sex':
                    patient_attribute_value = 'Female' if patient_attribute_value == 'F' else 'Male' if patient_attribute_value == 'M' else patient_attribute_value
                elif openmrs_attr in ['Citizenship', 'country']:
                    patient_attribute_value = '646'
                # Map OpenMRS attributes to DHIS2 attributes and append them to the attributes list
                # Replace province and district attribute values with the corresponding values from the province and district mappings
                if openmrs_attr == 'Province' and patient_attribute_value in province_mappings:
                    patient_attribute_value = province_mappings[patient_attribute_value]
                elif openmrs_attr == 'District':
                    # Handle cases where the attribute value is in the format "Rusizi / Western Province/Uburengerazuba"
                    if '/' in patient_attribute_value:
                        patient_attribute_value = patient_attribute_value.split('/')[0].strip()
                    if patient_attribute_value in district_mappings:
                        patient_attribute_value = district_mappings[patient_attribute_value]
                if patient_attribute_value is not None:
                    dhis2_compliant_json["attributes"].append({
                        "attribute": dhis2_attr,
                        "value": patient_attribute_value
                    })
            # Process each encounter
            for encounter_id in encounter_ids:
                # Fetch observations for the encounter
                observations = self.openmrs_connector.fetch_observations_for_encounter(encounter_id)
                # Load form mappings based on the form ID associated with the encounter
                form_id = self.openmrs_connector.get_form_id_by_encounter_id(encounter_id)
                form_mappings = self.load_form_mappings(form_id)
                # Transform encounter data and observations to DHIS2 event format
                event_data_values = []
                for observation in observations:
                    # Use form_mappings to map OpenMRS observation to DHIS2 data element
                    data_element_id = form_mappings['observations'].get(observation['concept_uuid'])
                    if data_element_id:
                        # Check if the dataElement is BCTuQ3xPYet and modify the value accordingly
                        if data_element_id == 'BCTuQ3xPYet':
                            if observation['value'] == 13467:
                                observation_value = 'random'
                            elif observation['value'] == 6689:
                                observation_value = 'fasting'
                            else:
                                observation_value = observation['value']
                        else:
                            observation_value = observation['value']
                        event_data_values.append({
                            "dataElement": data_element_id,
                            "value": observation_value
                        })
                # Log the event data values before appending to the enrollments list
                logging.info(f"Event data values for encounter ID {encounter_id}: {patient_data}")
                # Append transformed encounter data to the enrollments list
                dhis2_compliant_json["enrollments"].append({
                    # Fetch the location ID from the encounter data instead of patient_data
                    "orgUnit": location_mappings.get(location_id),
                    "program": form_mappings['dhis2_program_id'],  # Use the program stage ID from form mappings
                    "enrollmentDate": patient_data['date_created'],  # Use the date_created from patient data
                    "incidentDate": patient_data['date_created'],  # Use the date_created from patient data
                    "events": [{
                        "programStage": form_mappings['dhis2_program_stage_id'],  # Use the program stage ID from form mappings
                        "eventDate": self.openmrs_connector.get_encounter_date_created_by_id(encounter_id),  # Use the date_created from encounter data
                        "dataValues": event_data_values
                    }]
                })
            # Log the DHIS2-compliant JSON object to a new file named as the patient_id.json
            self.log_patient_data_to_sync_file(patient_id, dhis2_compliant_json)
            return dhis2_compliant_json
        except Exception as e:
            logging.error(f"Error processing patient ID {patient_id}: {e}")
            return {}


    def log_patient_data_to_sync_file(self, patient_id, dhis2_compliant_json):
        # Ensure the patients_to_sync directory exists
        os.makedirs('patients_to_sync', exist_ok=True)
        # Create a new JSON file for each patient using the patient ID as the filename
        file_path = os.path.join('patients_to_sync', f"{patient_id}.json")
        with open(file_path, 'w') as file:
            json.dump(dhis2_compliant_json, file, indent=4)

    # Other methods and logic as needed for the SyncService class
