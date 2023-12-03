import requests
import logging
import base64

class DHIS2Connector:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

    def get_auth_header(self):
        """Create the authorization header for DHIS2 API requests."""
        credentials = f"{self.username}:{self.password}"
        credentials_bytes = credentials.encode('ascii')
        base64_bytes = base64.b64encode(credentials_bytes)
        base64_credentials = base64_bytes.decode('ascii')
        return {"Authorization": f"Basic {base64_credentials}"}

    def make_api_call(self, endpoint, method='GET', data=None):
        """Make an API call to the DHIS2 instance."""
        url = f"{self.base_url}/{endpoint}"
        headers = self.get_auth_header()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            # Add other HTTP methods as needed
            response.raise_for_status()
            return response.json()
        except requests.RequestException as err:
            logging.error(f"Error in DHIS2 API call: {err}")
            raise

