from services.sync_service import SyncService
from utils.logger import setup_logger
from utils.progress_tracker import ProgressTracker
from config.settings import OPENMRS_DB_HOST, OPENMRS_DB_USER, OPENMRS_DB_PASSWORD, OPENMRS_DB_NAME, DHIS2_BASE_URL, DHIS2_USERNAME, DHIS2_PASSWORD

import sys

def main():
    # Set up logging
    setup_logger('logs/sync.log')

    # Welcome message
    print("Welcome to the OpenMRS to DHIS2 Synchronization Tool.")
    print("Please enter the location ID you want to sync data for:")
    
    # Get location ID from user
    location_id = input("Location ID: ").strip()
    if not location_id:
        print("No location ID provided. Exiting.")
        sys.exit(1)

    # Initialize progress tracker
    progress_tracker = ProgressTracker('logs/progress.json')

    # Check if the location has been handled before
    handled_locations = progress_tracker.get_progress('handled_locations') or {}
    if location_id in handled_locations:
        print(f"Location {location_id} has been handled before.")
        choice = input("Do you want to resume or start from scratch? (resume/scratch): ").strip().lower()
        if choice not in ['resume', 'scratch']:
            print("Invalid choice. Exiting.")
            sys.exit(1)
        elif choice == 'scratch':
            handled_locations[location_id] = []

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
    sync_service.sync(location_id, handled_locations.get(location_id), choice)

if __name__ == "__main__":
    main()

