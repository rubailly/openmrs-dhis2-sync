import mysql.connector
import logging

class OpenMRSConnector:
    def __init__(self, host, user, password, database):
        self.host = host.strip()
        self.user = user.strip()
        self.password = password.strip()
        self.database = database.strip()
        self.connection = None

    def fetch_encounter_ids_by_location(self, location_id, encounter_type_ids=None):
        """Fetch encounter IDs for a given location ID and optional encounter type IDs."""
        query = """
        SELECT encounter_id
        FROM encounter
        WHERE location_id = %s
        """
        query_params = [location_id]
        if encounter_type_ids:
            query += "AND encounter_type IN (%s)" % ', '.join(['%s'] * len(encounter_type_ids))
            query_params.extend(encounter_type_ids)
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (location_id,))
            result = cursor.fetchall()
            return [row[0] for row in result] if result else []
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

