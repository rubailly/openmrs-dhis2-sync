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
        """Load mappings for a specific form."""
        mapping_file = f'mappings/forms/form_{form_id}_mappings.json'
        if not os.path.exists(mapping_file):
            raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
        self.mappings[form_id] = load_mappings(mapping_file)

    def _transform_openmrs_to_dhis2_encounter(self, openmrs_observations, encounter_id, form_id):
        """Transform OpenMRS observations to the format required by DHIS2."""
        logging.info(f"Starting transformation of OpenMRS observations for encounter ID: {encounter_id}")
        try:
            # Ensure the form mappings are loaded
            if form_id not in self.mappings:
                self.load_form_mappings(form_id)
            form_mappings = self.mappings.get(form_id, {})
            if not form_mappings or 'observations' not in form_mappings:
                logging.error(f"No mappings found for form ID: {form_id}")
                return {}
            dhis2_program_stage_id = form_mappings.get('dhis2_program_stage_id')
            observation_mappings = form_mappings['observations']
            dhis2_data_elements = []
            for observation in openmrs_observations:
                concept_uuid = observation['concept_uuid']
                # Determine the appropriate value based on the observation's data type
                obs_value = observation['value'].get('numeric') or observation['value'].get('coded') or observation['value'].get('text') or observation['value'].get('datetime')
                dhis2_data_element_id = observation_mappings.get(concept_uuid)
                if dhis2_data_element_id and obs_value is not None:
                    dhis2_data_elements.append({
                        'dataElement': dhis2_data_element_id,
                        'value': obs_value
                    })
            transformed_encounter = {
                'programStage': dhis2_program_stage_id,
                'dataValues': dhis2_data_elements
            }
            logging.info(f"Transformed OpenMRS observations to DHIS2 format for encounter ID: {encounter_id}")
            return transformed_encounter
        except Exception as e:
            logging.exception(f"Error during transformation of OpenMRS observations for encounter ID {encounter_id}: {e}")
            return {}

    def _transform_dhis2_to_openmrs(self, dhis2_data):
        # Transform DHIS2 data to the format required by OpenMRS
        pass

    def _transform_openmrs_to_dhis2_patient(self, openmrs_patient_data):
        """Transform OpenMRS patient data to the format required by DHIS2."""
        logging.info(f"Starting transformation of OpenMRS patient data: {openmrs_patient_data}")
        try:
            # Ensure the location mappings are loaded
            if 'location' not in self.mappings:
                self.mappings['location'] = load_mappings('mappings/location_mappings.json')
            # Retrieve the location ID from the encounter data
            location_id = openmrs_patient_data.get('encounter_location_id')
            if location_id is None:
                logging.error("No location ID found in the encounter data.")
                return {}
            # Map the OpenMRS location ID to the DHIS2 organization unit ID
            dhis2_org_unit_id = self.mappings['location'].get(str(location_id))  # Convert location_id to string to match JSON keys
            if dhis2_org_unit_id is None:
                logging.error(f"No DHIS2 organization unit ID found for OpenMRS location ID: {location_id}")
                return {}
            # Add other patient transformations as needed
            # ...
            transformed_patient = {
                'orgUnit': dhis2_org_unit_id,
                # Include other DHIS2 patient attributes here
            }
            logging.info(f"Transformed OpenMRS patient data to DHIS2 format: {transformed_patient}")
            return transformed_patient
        except Exception as e:
            logging.exception(f"Error during transformation of OpenMRS patient data: {e}")
            return {}

    def fetch_observations_for_encounter(self, encounter_id):
        """Fetch all observations for a given encounter ID."""
        # Implementation of fetching observations from OpenMRS will go here
        pass

    def fetch_observations_for_encounter(self, encounter_id):
        """Fetch all observations for a given encounter ID."""
        return self.openmrs_connector.fetch_observations_for_encounter(encounter_id)

