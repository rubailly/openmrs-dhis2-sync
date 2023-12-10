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

def main():
    # Set up logging
    setup_logger('logs/sync.log')
    logging.info("Application started.")

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
    sync_service = SyncService(openmrs_config, dhis2_config, 'logs/progress.json')

    # Prompt user for encounter type IDs
    print("Please enter the encounter type IDs you are interested in (comma separated):")
    encounter_type_ids_input = input("Encounter Type IDs: ").strip()
    encounter_type_ids = encounter_type_ids_input.split(',') if encounter_type_ids_input else []

    # Connect to OpenMRS and fetch encounters by location ID and encounter type IDs
    logging.info("Attempting to connect to the OpenMRS database...")
    sync_service.openmrs_connector.connect()
    logging.info("Connection to OpenMRS database successful. Fetching encounters by location ID and encounter type IDs...")
    try:
        patient_encounters = sync_service.openmrs_connector.fetch_patient_encounters_by_location(location_id, encounter_type_ids)
        if patient_encounters is None:
            logging.error(f"Failed to fetch encounters for location ID {location_id}.")
            sys.exit(1)
        logging.info(f"Fetched encounters for {len(patient_encounters)} patients from the OpenMRS database for location ID {location_id}.")
        
                # Clear patients_to_sync.json and encounters_to_process.json files
        open('patients_to_sync.json', 'w').close()
        open('encounters_to_process.json', 'w').close()
    
        # Log the fetched patient encounters to the encounters_to_process.json file and process each patient's encounters
        with open('encounters_to_process.json', 'w') as file:
            json.dump(patient_encounters, file, indent=4)
        logging.info(f"Logged encounters for {len(patient_encounters)} patients to encounters_to_process.json.")


        # Read the encounters to process from the JSON file
        with open('encounters_to_process.json', 'r') as file:
            encounters_to_process = json.load(file)

        # Loop through each patient and process their encounters
        for patient_id, encounter_ids in encounters_to_process.items():
            # Process patient and their encounters
            sync_service.process_patient_and_encounters(patient_id, encounter_ids)

            # Ask the user if they want to continue to the next patient or cancel
            user_choice = input(f"Processed patient ID {patient_id}. Do you want to continue to the next patient? (yes/no): ").strip().lower()
            if user_choice != 'yes':
                print("Operation cancelled by the user.")
                break

            # Log the processed patient ID to the progress.json file
            progress_tracker.update_progress(location_id, patient_id)
    except Exception as e:
        logging.error(f"Failed to fetch encounters by location ID: {e}")
        sys.exit(1)

    # Exclude already handled encounters if resuming
    if choice == 'resume':
        encounter_ids = [eid for eid in encounter_ids if eid not in handled_encounters]

if __name__ == "__main__":
    main()

