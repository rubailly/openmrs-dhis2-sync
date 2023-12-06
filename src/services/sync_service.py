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
        self.mappings = {
            "location": load_mappings(mapping_files["location"]),
            "attribute": load_mappings(mapping_files["attribute"]),
            # Encounter mappings will be loaded dynamically based on form ID
        }
        self.progress_tracker = ProgressTracker(progress_tracker_file)

    # The above code is correct for transforming OpenMRS data to the DHIS2 format.
    # No changes are required here.

    def _transform_dhis2_to_openmrs(self, dhis2_data):
        # Transform DHIS2 data to the format required by OpenMRS
        pass

    def _transform_openmrs_to_dhis2_patient(self, openmrs_patient_data):
        # Transform OpenMRS patient data to DHIS2 format using the attribute mappings
        attribute_mappings = self.mappings['attribute']
        dhis2_attributes = []
        for openmrs_attr, dhis2_attr in attribute_mappings.items():
            if openmrs_attr in openmrs_patient_data and openmrs_patient_data[openmrs_attr] is not None:
                dhis2_attributes.append({
                    "attribute": dhis2_attr,
                    "value": openmrs_patient_data[openmrs_attr]
                })
    
        return {
            "trackedEntity": self.mappings['dhis2_tracked_entity_type'],
            "orgUnit": self.mappings['location'][openmrs_patient_data['location_uuid']],
            "attributes": dhis2_attributes
        }

    def _transform_openmrs_to_dhis2_encounter(self, openmrs_encounter_data, form_id):
        # Transform OpenMRS encounter data to DHIS2 format using the encounter mappings
        # Load form mappings based on form ID
        form_mappings_path = f'mappings/forms/form_{form_id}_mappings.json'
        form_mappings = load_mappings(form_mappings_path)
        
        encounter_mappings = form_mappings['observations']
        dhis2_data_elements = []
        for obs_uuid, dhis2_id in encounter_mappings.items():
            if obs_uuid in openmrs_encounter_data:
                dhis2_data_elements.append({
                    "dataElement": dhis2_id,
                    "value": openmrs_encounter_data[obs_uuid]
                })
        
        return {
            "programStage": self.mappings[form_id]['dhis2_program_stage_id'],
            "dataValues": dhis2_data_elements
        }

