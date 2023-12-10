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

        # Process patient encounters and build JSON objects
        with open('patients_to_sync.json', 'w') as file:
            for patient_id, encounter_ids in patient_encounters.items():
                logging.info(f"Processing encounters for patient ID: {patient_id}")
                # Fetch patient data and the first encounter data
                patient_data = sync_service.openmrs_connector.fetch_patient_data(patient_id)
                first_encounter_data = sync_service.openmrs_connector.fetch_observations_for_encounter(encounter_ids[0]) if encounter_ids else {}
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
                        logging.info(f"Fetched form ID: {form_id} for encounter ID: {encounter_id}")
                        transformed_encounter = sync_service._transform_openmrs_to_dhis2_encounter(observations, encounter_id, form_id)
                        logging.info(f"Transformed encounter data for encounter ID: {encounter_id}")
                        # Append transformed encounter data to the list
                        transformed_encounters.append(transformed_encounter)
                    except Exception as e:
                        logging.error(f"Failed to fetch or transform observations for encounter ID {encounter_id}: {e}")
                logging.info("Calling _combine_patient_and_encounters method.")
                # Transform patient data and encounters to DHIS2 format
                transformed_patient_data = sync_service._transform_openmrs_to_dhis2_patient(patient_data, first_encounter_data)
                # Combine patient data with their encounters into a DHIS2-compliant JSON object
                dhis2_compliant_json = sync_service._combine_patient_and_encounters(transformed_patient_data, transformed_encounters)
                # Log the combined patient and encounter data
                logging.info(f"Combined patient and encounter data: {json.dumps(dhis2_compliant_json, indent=4)}")
                # Print the combined patient and encounter data to the console
                print(json.dumps(dhis2_compliant_json, indent=4))
                # Ask the user whether to proceed to the next patient
                proceed = input("Proceed to the next patient? (y/n): ").strip().lower()
                if proceed != 'y':
                    print("Process canceled by the user.")
                    break
                # Write the combined patient and encounter data to the file
                json.dump(dhis2_compliant_json, file, indent=4)
                logging.info(f"Finished processing patient ID: {patient_id}")
                logging.info(f"Logged combined patient and encounter data for patient ID: {patient_id} to patients_to_sync.json")
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

