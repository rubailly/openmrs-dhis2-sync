import json
import os

class ProgressTracker:
    def __init__(self, file_path):
        self.file_path = file_path
        self.progress_data = self._load_progress()

    def _load_progress(self):
        """Load the synchronization progress from a file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return json.load(file)
        return {}

    def update_progress(self, key, value):
        """Update the progress for a specific key."""
        self.progress_data[key] = value
        with open(self.file_path, 'w') as file:
            json.dump(self.progress_data, file, indent=4)

    def get_progress(self, key):
        """Get the progress for a specific key."""
        return self.progress_data.get(key)

