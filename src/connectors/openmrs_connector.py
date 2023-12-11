import mysql.connector
import logging

class OpenMRSConnector:
    def __init__(self, host, user, password, database):
        self.host = host.strip()
        self.user = user.strip()
        self.password = password.strip()
        self.database = database.strip()
        self.connection = None

    def fetch_patient_encounters_by_location(self, location_id, form_ids=None):
        """Fetch patient encounters for a given location ID and list of form IDs, grouped by patient ID."""
        form_ids = form_ids or [197]  # Default form ID is 197 for mUzima NCD Screening Form
        form_ids_placeholder = ', '.join(['%s'] * len(form_ids))
        query = f"""
        SELECT patient_id, GROUP_CONCAT(encounter_id) as encounter_ids, date_created
        FROM encounter
        WHERE location_id = %s AND form_id IN ({form_ids_placeholder})
        GROUP BY patient_id
        """
        query_params = [location_id] + form_ids
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, query_params)
            result = cursor.fetchall()
            patient_encounters = {}
            for row in result:
                patient_encounters[row['patient_id']] = [int(eid) for eid in row['encounter_ids'].split(',')]
            return patient_encounters
        except mysql.connector.Error as err:
            logging.error(f"Error fetching encounter IDs: {err}")
            raise
        finally:
            if cursor:
                cursor.close()

    def fetch_patient_data(self, patient_id):
        """Fetch patient data for a given patient ID."""
        query = """
        SELECT patient_id, given_name, middle_name, family_name, gender, birthdate, date_created
        FROM patient
        JOIN person_name ON patient.patient_id = person_name.person_id
        JOIN person ON patient.patient_id = person.person_id
        WHERE patient.patient_id = %s AND person.voided = 0 AND person_name.voided = 0;
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (patient_id,))
            result = cursor.fetchone()
            return {
                'dhis2_tracked_entity_type': result['patient_id'],
                'First_Name': result.get('given_name', ''),
                'Middle_Name': result.get('middle_name', ''),
                'Family_Name': result.get('family_name', ''),
                'Sex': result.get('gender', ''),
                'Birthdate_Estimate': result['birthdate'].isoformat() if result and result['birthdate'] else None
            'date_created': result['date_created'].isoformat() if result and result['date_created'] else None
            } if result else {}
        except mysql.connector.Error as err:
            logging.error(f"Error fetching patient data for patient ID {patient_id}: {err}")
            raise
        finally:
            if cursor:
                cursor.close()

    def connect(self):
        """Establish a connection to the OpenMRS database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logging.info(f"Connected to the OpenMRS database at {self.host} successfully.")
        except Exception as err:
            logging.exception("Failed to connect to the OpenMRS database.")
            raise

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logging.info("OpenMRS database connection closed.")

    def fetch_observations_for_encounter(self, encounter_id):
        """Fetch all observations for a given encounter ID."""
        logging.info(f"Fetching observations for encounter ID: {encounter_id}")
        try:
            # The actual query should be defined here
            query = """
            SELECT obs.obs_id, concept.uuid AS concept_uuid, obs.value_numeric, obs.value_coded, obs.value_text, obs.value_datetime
            FROM obs
            JOIN concept ON obs.concept_id = concept.concept_id
            WHERE obs.encounter_id = %s
            """
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (encounter_id,))
            results = cursor.fetchall()
            logging.info(f"Fetched {len(results)} observations for encounter ID: {encounter_id}")
            observations = []
            for result in results:
                logging.debug(f"Processing observation: {result}")
                # Create an OpenMRSObservation object for each observation
                observations.append({
                    'obs_id': result['obs_id'],
                    'concept_uuid': result['concept_uuid'],
                    'value': {
                        'numeric': result['value_numeric'],
                        'coded': result['value_coded'],
                        'text': result['value_text'],
                        'datetime': result['value_datetime'].isoformat() if result['value_datetime'] else None
                    }
                })
            return observations
        except mysql.connector.Error as err:
            logging.exception(f"Error fetching observations for encounter ID {encounter_id}: {err}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_encounter_date_created_by_id(self, encounter_id):
        """Fetch the date_created for a given encounter ID."""
        query = """
        SELECT date_created
        FROM encounter
        WHERE encounter_id = %s
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (encounter_id,))
            result = cursor.fetchone()
            return result['date_created'].isoformat() if result and result['date_created'] else None
        except mysql.connector.Error as err:
            logging.error(f"Error fetching date_created for encounter ID {encounter_id}: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
        try:
            cursor = self.connection.cursor(dictionary=True)
            logging.info(f"Executing query for encounter ID: {encounter_id}")
            cursor.execute(query, (encounter_id,))
            result = cursor.fetchone()
            cursor.fetchall()  # Fetch the remaining results to avoid the "Unread result found" error
            logging.info(f"Query executed for encounter ID: {encounter_id}")
            # Convert date objects to strings in ISO format
            if result and 'Birth_Date' in result and result['Birth_Date']:
                result['Birth_Date'] = result['Birth_Date'].isoformat()
            return result
        except mysql.connector.Error as err:
            logging.error(f"Error fetching patient data: {err}")
            raise
        finally:
            cursor.close()

    def get_encounter_type_id_by_form_id(self, form_id):
        """Fetch the encounter type ID for a given form ID."""
        query = """
        SELECT encounter_type_id
        FROM encounter_type
        WHERE uuid = %s
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (form_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except mysql.connector.Error as err:
            logging.error(f"Error fetching encounter type ID: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
