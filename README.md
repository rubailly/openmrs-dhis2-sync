
# OpenMRS to DHIS2 Synchronization Tool

## Overview
The OpenMRS to DHIS2 Synchronization Tool (`openmrs-dhis2-sync`) is designed to facilitate the seamless transfer and synchronization of patient data and health observations from OpenMRS to DHIS2. This tool ensures data consistency, integrity, and reliability across both health information systems.

### Key Features
- Synchronization of patient data from OpenMRS to DHIS2.
- Mapping of OpenMRS concepts to DHIS2 data elements.
- Location-based data processing for manageable and organized data handling.
- Robust error handling and logging for reliable operation.
- Progress tracking to resume operation in case of interruption.

## Installation

### Prerequisites
- Python 3.x
- Git
- Access to OpenMRS and DHIS2 instances with necessary permissions.

### Setup
1. Clone the repository:
   ```
   git clone https://github.com/rubailly/openmrs-dhis2-sync.git
   ```
2. Navigate to the project directory:
   ```
   cd openmrs-dhis2-sync
   ```
3. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Unix or MacOS
   venv\Scripts\activate     # On Windows
   ```
4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration
Before running the tool, configure the following:

- `.env`: Set the environment variables for API keys, database URLs, etc.
- `mappings/`: Update the JSON mapping files to align OpenMRS concepts with DHIS2 data elements.

## Usage
To run the synchronization process:
```
python src/main.py
```

## Structure
The repository is structured as follows:
- `src/`: Contains the source code with various subdirectories for different modules.
- `tests/`: Includes test suites for the application.
- `mappings/`: Stores JSON or YAML files for data mappings.
- `logs/`: Contains log files for the synchronization process.
- `requirements.txt`: Lists all the Python dependencies.
- `README.md`: Provides documentation for the repository.

## Contributing
Contributions to improve `openmrs-dhis2-sync` are welcome. Please follow these steps to contribute:
1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Commit your changes with clear, descriptive messages.
4. Push the branch and create a pull request.

## License
Specify the license under which this project is released.

## Acknowledgements
Include any acknowledgements, credits, or references used in the development of this tool.

---

For more detailed information about each component and its functionality, refer to the documentation within each module's directory.
