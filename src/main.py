from services.sync_service import SyncService
from utils.logger import setup_logger
from utils.progress_tracker import ProgressTracker
from config.settings import OPENMRS_DB_HOST, OPENMRS_DB_USER, OPENMRS_DB_PASSWORD, OPENMRS_DB_NAME, DHIS2_BASE_URL, DHIS2_USERNAME, DHIS2_PASSWORD

def main():
    # Set up logging
    setup_logger('logs/sync.log')

    # Initialize progress tracker
    progress_tracker = ProgressTracker('logs/progress.json')

    # Configuration for OpenMRS and DHIS2 connectors
    openmrs_config = {
        "host": OPENMRS_DB_HOST,
        "user": OPENMRS_DB_USER,
        "password": OPENMRS_DB_PASSWORD,
        "database": OPENMRS_DB_NAME
    }
    dhis2_config = {
        "base_url": DHIS2_BASE_URL,
        "username": DHIS2_USERNAME,
        "password": DHIS2_PASSWORD
    }

    # Initialize the SyncService
    sync_service = SyncService(openmrs_config, dhis2_config, {
        "location": 'mappings/location_mappings.json',
        "attribute": 'mappings/attribute_mappings.json',
        "observation": 'mappings/observation_mappings.json'
    })

    # Start the synchronization process
    sync_service.sync()

if __name__ == "__main__":
    main()

