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

    def reset_progress(self, location_id):
        """Reset the progress for a specific location."""
        if location_id in self.progress_data:
            del self.progress_data[location_id]
            self._save_progress()

    def update_progress(self, key, value, reset=False):
        """Update the progress for a specific key."""
        if reset:
            self.reset_progress(key)
        else:
            self.progress_data[key] = value
        self._save_progress()

    def _save_progress(self):
        """Save the progress data to the file."""
        with open(self.file_path, 'w') as file:
            json.dump(self.progress_data, file, indent=4)

    def get_progress(self, key):
        """Get the progress for a specific key."""
        return self.progress_data.get(key)

