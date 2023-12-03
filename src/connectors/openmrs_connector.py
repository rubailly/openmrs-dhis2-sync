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
            logging.info("Connected to the OpenMRS database.")
            print("Successfully connected to the OpenMRS database.")
        except mysql.connector.Error as err:
            logging.error(f"Error connecting to the OpenMRS database: {err}")
            raise

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logging.info("OpenMRS database connection closed.")

    def execute_query(self, query, params=None):
        """Execute a given SQL query on the OpenMRS database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Error executing query: {err}")
            raise
        finally:
            cursor.close()

