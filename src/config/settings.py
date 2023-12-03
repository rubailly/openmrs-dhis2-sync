# settings.py
import os

# Load environment variables
OPENMRS_DB_HOST = os.getenv("OPENMRS_DB_HOST")
OPENMRS_DB_USER = os.getenv("OPENMRS_DB_USER")
OPENMRS_DB_PASSWORD = os.getenv("OPENMRS_DB_PASSWORD")
OPENMRS_DB_NAME = os.getenv("OPENMRS_DB_NAME")

DHIS2_BASE_URL = os.getenv("DHIS2_BASE_URL")
DHIS2_USERNAME = os.getenv("DHIS2_USERNAME")
DHIS2_PASSWORD = os.getenv("DHIS2_PASSWORD")

