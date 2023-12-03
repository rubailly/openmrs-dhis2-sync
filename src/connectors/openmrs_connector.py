import mysql.connector
import logging

class OpenMRSConnector:
    def __init__(self, host, user, password, database):
        self.host = host.strip()
        self.user = user.strip()
        self.password = password.strip()
        self.database = database.strip()
        self.connection = None

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
        -- Additional fields and joins here
        FROM patient p
        INNER JOIN person per ON p.patient_id = per.person_id
        -- Additional joins here
        WHERE p.encounter_id = %s
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (encounter_id,))
            return cursor.fetchone()
        except mysql.connector.Error as err:
            logging.error(f"Error fetching patient data: {err}")
            raise
        finally:
            cursor.close()

