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
        SELECT patient_id, GROUP_CONCAT(encounter_id) as encounter_ids
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
        query = """
        SELECT obs_id, concept_id, value_numeric, value_coded, value_text, value_datetime
        FROM obs
        WHERE encounter_id = %s AND voided = 0;
        """
        logging.info(f"Fetching observations for encounter ID: {encounter_id}")
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (encounter_id,))
            results = cursor.fetchall()
            logging.info(f"Fetched {len(results)} observations for encounter ID: {encounter_id}")
            observations = []
            for result in results:
                logging.debug(f"Processing observation: {result}")
                # Create an OpenMRSObservation object for each observation
                observation = OpenMRSObservation(
                    obs_id=result['obs_id'],
                    value={
                        'numeric': result['value_numeric'],
                        'coded': result['value_coded'],
                        'text': result['value_text'],
                        'datetime': result['value_datetime'].isoformat() if result['value_datetime'] else None
                    }
                )
                observations.append(observation)
            return observations
        except mysql.connector.Error as err:
            logging.exception(f"Error fetching observations for encounter ID {encounter_id}: {err}")
            raise
        # The second finally block is redundant and should be removed.

    def fetch_patient_data(self, encounter_id):
        """Fetch patient data for a given encounter ID."""
        query = """
        SELECT p.patient_id, pn.given_name AS First_Name, pn.middle_name AS Middle_Name, pn.family_name AS Family_Name, nat.identifier AS National_ID,
        (SELECT pa.value FROM person_attribute pa WHERE pa.person_id = per.person_id AND pa.person_attribute_type_id = (SELECT person_attribute_type_id FROM person_attribute_type WHERE uuid = '8b908adf-c964-4959-ad43-e2c7aeaa9c67')) AS Phone_Number, -- UUID for Phone Number
        (SELECT pa.value FROM person_attribute pa WHERE pa.person_id = per.person_id AND pa.person_attribute_type_id = (SELECT person_attribute_type_id FROM person_attribute_type WHERE uuid = '678b3499-81cd-4a26-9577-4dc1efcf0510')) AS Citizenship, -- UUID for Citizenship
        (SELECT pa.value FROM person_attribute pa WHERE pa.person_id = per.person_id AND pa.person_attribute_type_id = (SELECT person_attribute_type_id FROM person_attribute_type WHERE uuid = '8d87236c-c2cc-11de-8d13-0010c6dffd0f')) AS Health_Facility, -- UUID for Health Facility
        addr.country, addr.state_province AS Province, addr.county_district AS District, addr.city_village AS Sector, addr.address3 AS Cell, addr.address1 AS Village,
        per.gender AS Sex, per.birthdate AS Birth_Date, per.birthdate_estimated AS Birthdate_Estimate, FLOOR(DATEDIFF(CURRENT_DATE, per.birthdate) / 365) AS Age_in_Years
        FROM encounter e
        INNER JOIN patient p ON e.patient_id = p.patient_id
        INNER JOIN person per ON p.patient_id = per.person_id
        LEFT JOIN person_name pn ON per.person_id = pn.person_id
        LEFT JOIN patient_identifier nat ON p.patient_id = nat.patient_id AND nat.identifier_type = '85c63542-587f-476c-9e69-c733bd285a57' -- UUID for National ID
        LEFT JOIN person_address addr ON per.person_id = addr.person_id
        WHERE e.encounter_id = %s;
        """
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
