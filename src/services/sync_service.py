import os
from connectors.openmrs_connector import OpenMRSConnector
from connectors.dhis2_connector import DHIS2Connector
from models.dhis2_models import DHIS2TrackedEntity, DHIS2DataElement
from models.openmrs_models import OpenMRSPatient, OpenMRSObservation
from config.mappings import load_mappings
from utils.progress_tracker import ProgressTracker

class SyncService:
    def __init__(self, openmrs_config, dhis2_config, mapping_files, progress_tracker_file):
        self.openmrs_connector = OpenMRSConnector(**openmrs_config)
        self.dhis2_connector = DHIS2Connector(**dhis2_config)
        self.mapping_files = mapping_files
        self._validate_and_load_mappings()
        
    def _validate_and_load_mappings(self):
        """Validate and load mappings from provided file paths."""
        if not self.mapping_files:
            raise ValueError("Mapping file paths are not provided.")
        for key, file_path in self.mapping_files.items():
            if not file_path:
                raise ValueError(f"Mapping file path for '{key}' is not provided.")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Mapping file not found: {file_path}")
            self.mappings[key] = load_mappings(file_path)
        self.progress_tracker = ProgressTracker(progress_tracker_file)

    def _transform_openmrs_to_dhis2_encounter(self, openmrs_encounter_data, form_id):
        """Transform OpenMRS encounter data to the format required by DHIS2."""
        # Load the form mappings based on the form ID
        form_mappings = load_mappings(self.mapping_files.get(form_id))
        dhis2_program_stage_id = form_mappings.get('dhis2_program_stage_id')
        dhis2_data_elements = []
        # Assuming openmrs_encounter_data is a list of observation dictionaries
        for observation in openmrs_encounter_data:
            concept_uuid = observation['concept_uuid']
            value = observation['value']
            # Determine the appropriate value based on the observation's data type
            obs_value = value.get('numeric') or value.get('coded') or value.get('text') or value.get('datetime')
            dhis2_data_element_id = form_mappings['observations'].get(concept_uuid)
            if dhis2_data_element_id and obs_value is not None:
                dhis2_data_elements.append({
                    'dataElement': dhis2_data_element_id,
                    'value': obs_value
                })
        # Add other encounter transformations as needed
        # ...
        return {
            'programStage': dhis2_program_stage_id,
            'dataValues': dhis2_data_elements
        }

    def _transform_dhis2_to_openmrs(self, dhis2_data):
        # Transform DHIS2 data to the format required by OpenMRS
        pass

    def _transform_openmrs_to_dhis2_patient(self, openmrs_patient_data):
        """Transform OpenMRS patient data to the format required by DHIS2."""
        # Map the OpenMRS location ID to the DHIS2 organization unit ID
        location_id = openmrs_patient_data.get('location_id')
        dhis2_org_unit_id = self.mappings['location'].get(location_id)
        # Add other patient transformations as needed
        # ...
        return {
            'orgUnit': dhis2_org_unit_id,
            # Include other DHIS2 patient attributes here
        }

    def fetch_observations_for_encounter(self, encounter_id):
        """Fetch all observations for a given encounter ID."""
        # Implementation of fetching observations from OpenMRS will go here
        pass

    def fetch_observations_for_encounter(self, encounter_id):
        """Fetch all observations for a given encounter ID."""
        return self.openmrs_connector.fetch_observations_for_encounter(encounter_id)

