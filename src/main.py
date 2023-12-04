import logging
import json
import sys
from dotenv import load_dotenv
from services.sync_service import SyncService
from utils.logger import setup_logger
from utils.progress_tracker import ProgressTracker

# Load environment variables
load_dotenv()
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

    # Check if the location has been handled before or if it's new
    handled_encounters = progress_tracker.get_progress(location_id)
    if handled_encounters is not None:
        print(f"Location {location_id} has been handled before.")
        choice = input("Do you want to resume or start from scratch? (resume/scratch): ").strip().lower()
        if choice not in ['resume', 'scratch']:
            print("Invalid choice. Exiting.")
            sys.exit(1)
        elif choice == 'scratch':
            handled_encounters = []
            progress_tracker.reset_progress(location_id)
    else:
        print(f"Location {location_id} is new. Starting the process of selecting all encounters for this location.")
        handled_encounters = []
        choice = 'scratch'

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
    }, 'logs/progress.json')

    # Connect to OpenMRS and fetch encounters by location ID
    logging.info("Attempting to connect to the OpenMRS database...")
    sync_service.openmrs_connector.connect()
    logging.info("Connection to OpenMRS database successful. Fetching encounters by location ID...")
    try:
        encounter_ids = sync_service.openmrs_connector.fetch_encounter_ids_by_location(location_id)
        logging.info(f"Fetched {len(encounter_ids)} encounters from the OpenMRS database for location ID {location_id}.")
    
        # Log the fetched encounter IDs to the encounters_to_process.json file
        with open('encounters_to_process.json', 'w') as file:
            json.dump(encounter_ids, file, indent=4)
        logging.info(f"Logged {len(encounter_ids)} encounter IDs to encounters_to_process.json.")

        # Log the fetched encounter IDs to the progress.json file
        progress_tracker.update_progress(location_id, encounter_ids, reset=True)
    except Exception as e:
        logging.error(f"Failed to fetch encounters by location ID: {e}")
        sys.exit(1)

    # Exclude already handled encounters if resuming
    if choice == 'resume':
        encounter_ids = [eid for eid in encounter_ids if eid not in handled_encounters]

    # Process encounters and build JSON objects
    patient_data_list = []
    for encounter_id in encounter_ids:
        patient_data = sync_service.openmrs_connector.fetch_patient_data(encounter_id)
        if patient_data:
            patient_data_list.append(patient_data)
        else:
            logging.warning(f"No patient data found for encounter ID {encounter_id}")
    
    # Log the JSON objects to a file
    with open('patients_to_sync.json', 'w') as file:
        json.dump(patient_data_list, file, indent=4)
    print(f"Logged {len(patient_data_list)} patient JSON objects to process.")

    # Start the synchronization process
    sync_service.sync(location_id, encounter_ids, choice)

if __name__ == "__main__":
    main()

