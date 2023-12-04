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
        self.mappings = {key: load_mappings(file) for key, file in mapping_files.items()}
        self.progress_tracker = ProgressTracker(progress_tracker_file)

    def sync(self, location_id, handled_encounters, choice):
        # Check if we need to reset progress
        if choice == 'scratch':
            self.progress_tracker.reset_progress(location_id)
        # Implement the synchronization logic here
        # This might include fetching data from OpenMRS, transforming it, 
        # and then sending it to DHIS2, or vice versa.
        # Use `handled_encounters` to determine what has already been processed.

    def _transform_openmrs_to_dhis2(self, openmrs_data, form_id):
        # Load the form-specific mappings based on the form_id
        form_mappings = self.mappings.get("forms", {}).get(form_id, {})
        if not form_mappings:
            raise ValueError(f"No mappings found for form ID: {form_id}")

        # Initialize the DHIS2 event structure
        dhis2_event = {
            "program": form_mappings.get("dhis2_program_id"),
            "orgUnit": self.mappings["location"].get(openmrs_data["Health_Facility"]),
            "eventDate": openmrs_data["encounter_datetime"].split("T")[0],  # Assuming encounter_datetime is in ISO format
            "status": "COMPLETED",
            "programStage": form_mappings.get("dhis2_program_stage_id"),
            "dataValues": []
        }

        # Map OpenMRS observations to DHIS2 data elements
        for obs_uuid, value in openmrs_data.get("observations", {}).items():
            dhis2_data_element_id = form_mappings["observations"].get(obs_uuid)
            if dhis2_data_element_id:
                dhis2_event["dataValues"].append({
                    "dataElement": dhis2_data_element_id,
                    "value": value
                })

        # Map OpenMRS patient attributes to DHIS2 tracked entity attributes
        for attr, attr_value in openmrs_data.items():
            dhis2_attribute_id = self.mappings["attribute"].get(attr)
            if dhis2_attribute_id:
                dhis2_event["dataValues"].append({
                    "dataElement": dhis2_attribute_id,
                    "value": attr_value
                })

        return dhis2_event

    def _transform_dhis2_to_openmrs(self, dhis2_data):
        # Transform DHIS2 data to the format required by OpenMRS
        pass

    # Additional methods as needed

