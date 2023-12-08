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

    # No changes needed here, this is just for review purposes

    def _transform_dhis2_to_openmrs(self, dhis2_data):
        # Transform DHIS2 data to the format required by OpenMRS
        pass

    def _transform_openmrs_to_dhis2_patient(self, openmrs_patient_data, openmrs_encounter_data):
        """Transform OpenMRS patient data to the format required by DHIS2."""
        logging.info(f"Starting transformation of OpenMRS patient data: {openmrs_patient_data}")
        try:
            # Ensure the location mappings are loaded
            if 'location' not in self.mappings:
                self.mappings['location'] = load_mappings('mappings/location_mappings.json')
            # Retrieve the location ID from the encounter data
            location_id = openmrs_encounter_data.get('location_id')
            if location_id is None:
                logging.error("No location ID found in the encounter data for patient ID: " + str(openmrs_patient_data.get('patient_id')))
                return {}
            # Map the OpenMRS location ID to the DHIS2 organization unit ID
            dhis2_org_unit_id = self.mappings['location'].get(str(location_id))  # Convert location_id to string to match JSON keys
            if dhis2_org_unit_id is None:
                logging.error(f"No DHIS2 organization unit ID found for OpenMRS location ID: {location_id}")
                return {}
            # Retrieve the encounter date from the encounter data and format it correctly
            date_created = openmrs_encounter_data.get('date_created')
            encounter_date = date_created.strftime('%Y-%m-%d') if date_created and isinstance(date_created, datetime.datetime) else None
            # Add other patient transformations as needed
            # ...
            transformed_patient = {
                'orgUnit': dhis2_org_unit_id,
                'program': 'L4DxA2Y3mqQ',  # Hardcoded DHIS2 program value
                'enrollmentDate': encounter_date,  # Use the encounter date for enrollment
                'incidentDate': encounter_date,  # Use the encounter date for incident
                # Include other DHIS2 patient attributes here
            }
            logging.info(f"Finished transforming OpenMRS patient data to DHIS2 format: {transformed_patient}")
            return transformed_patient
        except Exception as e:
            logging.exception(f"Error during transformation of OpenMRS patient data: {e}")
            return {}

    def fetch_observations_for_encounter(self, encounter_id):
        """Fetch all observations for a given encounter ID."""
        # Implementation of fetching observations from OpenMRS will go here
        pass

    def _transform_openmrs_to_dhis2_encounter(self, observations, encounter_id, form_id):
        """Transform OpenMRS encounter data to the format required by DHIS2."""
        logging.info(f"Starting transformation of OpenMRS encounter data for encounter ID: {encounter_id}")
        try:
            # Load the form mappings
            form_mappings = self.load_form_mappings(form_id)
            if not form_mappings:
                logging.error(f"No mappings found for form ID: {form_id}")
                return {}
            dhis2_program_stage_id = form_mappings['dhis2_program_stage_id']
            if not dhis2_program_stage_id:
                logging.error(f"No DHIS2 program stage ID found for form ID: {form_id}")
                return {}
            # Initialize the list of DHIS2 data elements
            data_elements = []
            for obs in observations:
                concept_uuid = obs.get('concept_uuid')
                dhis2_data_element_id = form_mappings.get('observations', {}).get(concept_uuid)
                if dhis2_data_element_id:
                    data_elements.append({
                        'dataElement': dhis2_data_element_id,
                        'value': obs.get('value')
                    })
            # Construct the DHIS2 event
            dhis2_event = {
                'programStage': dhis2_program_stage_id,
                'dataValues': data_elements
            }
            logging.info(f"Finished transforming OpenMRS encounter data to DHIS2 event: {dhis2_event}")
            return dhis2_event
        except Exception as e:
            logging.exception(f"Error during transformation of OpenMRS encounter data: {e}")
            return {}

    def _combine_patient_and_encounters(self, transformed_patient_data, transformed_encounters):
        """Combine patient data and encounters into a single DHIS2-compliant JSON object."""
        try:
            logging.info("_combine_patient_and_encounters method called.")
        # Log the values retrieved from transformed_patient_data
        logging.info(f"Retrieved 'trackedEntityInstance': {transformed_patient_data.get('trackedEntityInstance')}")
        logging.info(f"Retrieved 'program': {transformed_patient_data.get('program')}")
        logging.info(f"Retrieved 'enrollmentDate': {transformed_patient_data.get('enrollmentDate')}")
        logging.info(f"Retrieved 'incidentDate': {transformed_patient_data.get('incidentDate')}")

        # Use the orgUnit from the transformed patient data
        org_unit = transformed_patient_data.get('orgUnit')
        # Log the orgUnit value
        logging.info(f"Retrieved 'orgUnit': {org_unit}")

        # Map patient attributes to DHIS2 format
        attributes = self._map_patient_attributes_to_dhis2(transformed_patient_data)
        # Log the attributes
        logging.info(f"Patient attributes for DHIS2: {attributes}")

        # Combine patient attributes and encounters into a single data structure
        combined_data = {
            "trackedEntityInstance": transformed_patient_data.get('trackedEntityInstance'),
            "orgUnit": org_unit,
            "attributes": attributes,
            "enrollments": [
                {
                    "orgUnit": org_unit,
                    "program": transformed_patient_data.get('program'),
                    "enrollmentDate": transformed_patient_data.get('enrollmentDate'),
                    "incidentDate": transformed_patient_data.get('incidentDate'),
                    "events": transformed_encounters
                }
            ]
        }
        # Log the combined patient and encounter data
        logging.info(f"Combined patient and encounter data into a single DHIS2-compliant JSON object: {json.dumps(combined_data, indent=4)}")
        # Log the combined patient and encounter data
        logging.info(f"Combined patient and encounter data into a single DHIS2-compliant JSON object: {json.dumps(combined_data, indent=4)}")
        return combined_data

