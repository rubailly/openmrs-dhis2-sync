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
    
        # Log the fetched patient encounters to the encounters_to_process.json file and process each patient's encounters
        with open('encounters_to_process.json', 'w') as file:
            json.dump(patient_encounters, file, indent=4)
        logging.info(f"Logged encounters for {len(patient_encounters)} patients to encounters_to_process.json.")

        # Clear patients_to_sync.json and encounters_to_process.json files
        open('patients_to_sync.json', 'w').close()
        open('encounters_to_process.json', 'w').close()

        # Process patient encounters and build JSON objects
        with open('patients_to_sync.json', 'w') as file:
            for patient_id, encounter_ids in patient_encounters.items():
                logging.info(f"Processing encounters for patient ID: {patient_id}")
                # Fetch patient data using the first encounter ID
                patient_data = sync_service.openmrs_connector.fetch_patient_data(patient_id)
                # Initialize a list to hold all transformed encounters
                transformed_encounters = []
                for encounter_id in encounter_ids:
                    logging.info(f"Fetching observations for encounter ID: {encounter_id}")
                    try:
                        # Fetch all observations for the encounter
                        observations = sync_service.openmrs_connector.fetch_observations_for_encounter(encounter_id) 
                        logging.info(f"Fetched {len(observations)} observations for encounter ID: {encounter_id}")
                        # Transform encounter data and observations to DHIS2 format
                        # Fetch the form ID for the encounter
                        form_id = sync_service.openmrs_connector.get_form_id_by_encounter_id(encounter_id)
                        transformed_encounter = sync_service._transform_openmrs_to_dhis2_encounter(observations, encounter_id, form_id)
                        logging.info(f"Transformed encounter data for encounter ID: {encounter_id}")
                        # Append transformed encounter data to the list
                        transformed_encounters.append(transformed_encounter)
                    except Exception as e:
                        logging.error(f"Failed to fetch or transform observations for encounter ID {encounter_id}: {e}")
                # Combine patient data with their encounters
                transformed_patient_data = sync_service._transform_openmrs_to_dhis2_patient(patient_data)
                # Initialize encounters list in the transformed patient data
                transformed_patient_data['encounters'] = transformed_encounters
                # Print the transformed patient data to the console
                print(json.dumps([transformed_patient_data], indent=4))  # Wrap patient_data in a list to maintain JSON array format
                # Ask the user whether to proceed to the next patient
                proceed = input("Proceed to the next patient? (y/n): ").strip().lower()
                if proceed != 'y':
                    print("Process canceled by the user.")
                    break
                # Write the transformed patient data to the file
                json.dump([transformed_patient_data], file, indent=4)
                logging.info(f"Finished processing patient ID: {patient_id}")
                logging.info(f"Logged patient data with encounters for patient ID: {patient_id} to patients_to_sync.json")
            else:
                logging.warning(f"No patient data found for patient ID {patient_id}")

        # Log the fetched encounter IDs to the progress.json file
        progress_tracker.update_progress(location_id, encounter_ids, reset=True)
    except Exception as e:
        logging.error(f"Failed to fetch encounters by location ID: {e}")
        sys.exit(1)

    # Exclude already handled encounters if resuming
    if choice == 'resume':
        encounter_ids = [eid for eid in encounter_ids if eid not in handled_encounters]

if __name__ == "__main__":
    main()

