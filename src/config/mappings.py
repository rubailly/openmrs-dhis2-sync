# mappings.py
import json

def load_mappings(file_path):
    """Load mappings from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception(f"Mapping file not found: {file_path}")

