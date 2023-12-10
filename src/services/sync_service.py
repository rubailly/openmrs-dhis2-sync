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

    def process_patient_and_encounters(self, patient_id, encounter_ids):
        """Process a patient and their encounters, transforming them into a DHIS2-compliant JSON object ready for submission to DHIS2."""
        logging.info(f"Processing patient ID: {patient_id}")
        # Load attribute mappings
        attribute_mappings = load_mappings('mappings/attribute_mappings.json')
        # Load location mappings
        location_mappings = load_mappings('mappings/location_mappings.json')
        # Initialize the DHIS2-compliant JSON object
        dhis2_compliant_json = {
            "trackedEntityInstance": patient_id,  # Assuming patient_id is used as trackedEntityInstance
            "attributes": [],
            "enrollments": []
        }
        try:
            # Fetch patient data
            patient_data = self.openmrs_connector.fetch_patient_data(patient_id)
            # Transform patient data to DHIS2 attributes format
            for attribute_name, attribute_value in patient_data.items():
                # Map the OpenMRS attribute names to the corresponding DHIS2 attribute IDs
                dhis2_attribute_id = attribute_mappings.get(attribute_name)
                if dhis2_attribute_id and attribute_value is not None:
                    dhis2_compliant_json["attributes"].append({
                        "attribute": dhis2_attribute_id,
                        "value": attribute_value
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
                        event_data_values.append({
                            "dataElement": data_element_id,
                            "value": observation['value']
                        })
                # Log the event data values before appending to the enrollments list
                logging.info(f"Event data values for encounter ID {encounter_id}: {patient_data}")
                # Append transformed encounter data to the enrollments list
                dhis2_compliant_json["enrollments"].append({
                    # Fetch the location ID from the encounter data instead of patient_data
                    "orgUnit": location_mappings.get(str(366)),
                    "program": form_mappings['dhis2_program_stage_id'],  # Use the program stage ID from form mappings
                    "enrollmentDate": "YYYY-MM-DD",  # Placeholder for actual enrollment date
                    "incidentDate": "YYYY-MM-DD",  # Placeholder for actual incident date
                    "events": [{
                        "programStage": form_mappings['dhis2_program_stage_id'],  # Use the program stage ID from form mappings
                        "eventDate": "YYYY-MM-DD",  # Placeholder for actual event date
                        "dataValues": event_data_values
                    }]
                })
            # Log the DHIS2-compliant JSON object to a file for synchronization
            self.log_patient_data_to_sync_file(dhis2_compliant_json)
            return dhis2_compliant_json
        except Exception as e:
            logging.error(f"Error processing patient ID {patient_id}: {e}")
            return {}


    def log_patient_data_to_sync_file(self, dhis2_compliant_json):
        # Implement logging logic
        # This will log the DHIS2-compliant JSON object to a file for synchronization
        with open('patients_to_sync.json', 'w') as file:
            json.dump(dhis2_compliant_json, file, indent=4)

    # Other methods and logic as needed for the SyncService class
