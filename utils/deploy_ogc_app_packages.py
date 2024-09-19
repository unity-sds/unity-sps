import argparse
import json
import logging
import os

import unity_sps_ogc_processes_api_python_client
from unity_sps_ogc_processes_api_python_client.models.ogcapppkg import Ogcapppkg
from unity_sps_ogc_processes_api_python_client.rest import ApiException

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def register_process(api_instance, proc, ogcapppkg_instance):
    """
    Register a process with the OGC API.

    Args:
        api_instance: The API client instance.
        proc: The process identifier.
        ogcapppkg_instance: The Ogcapppkg instance containing the process description.

    Returns:
        None
    """
    try:
        # Deploy a process
        api_instance.deploy_processes_post(w=proc, ogcapppkg=ogcapppkg_instance)
        logging.info(f"Successfully registered process: {proc}")
    except ApiException as e:
        logging.error(f"Exception when calling DRUApi->deploy_processes_post for process {proc}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error for process {proc}: {e}")


def main():
    """
    Main function to deploy processes to the OGC API.

    Parses command-line arguments, reads process descriptions from JSON files,
    and registers each process with the OGC API.

    Args:
        None

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description="Deploy processes to OGC API")
    parser.add_argument("ogc_api_processes", help="OGC API Processes URL")
    parser.add_argument(
        "ogc_app_packages_dir", help="Directory containing JSON files with application packages"
    )
    args = parser.parse_args()

    OGC_API_PROCESSES = args.ogc_api_processes
    ogc_app_packages_dir = args.ogc_app_packages_dir

    # Configure the API client
    configuration = unity_sps_ogc_processes_api_python_client.Configuration(host=OGC_API_PROCESSES)

    with unity_sps_ogc_processes_api_python_client.ApiClient(configuration) as api_client:
        api_instance = unity_sps_ogc_processes_api_python_client.DRUApi(api_client)

        # Iterate through all JSON files in the specified directory
        for filename in os.listdir(ogc_app_packages_dir):
            if filename.endswith(".json"):
                json_file = os.path.join(ogc_app_packages_dir, filename)
                try:
                    # Read the process description from the JSON file
                    with open(json_file, "r") as f:
                        process_data = json.load(f)

                    # Extract the process ID from the JSON data
                    proc = process_data.get("processDescription", {}).get("id")
                    if not proc:
                        logging.error(f"Process ID not found in JSON file: {json_file}")
                        continue

                    # Create an instance of Ogcapppkg from the JSON data
                    ogcapppkg_instance = Ogcapppkg.from_dict(process_data)
                    logging.info(f"Registering process: {proc}")
                    register_process(api_instance, proc, ogcapppkg_instance)
                except FileNotFoundError:
                    logging.error(f"JSON file not found: {json_file}")
                except json.JSONDecodeError:
                    logging.error(f"Error decoding JSON file: {json_file}")
                except Exception as e:
                    logging.error(f"Unexpected error processing file {json_file}: {e}")


if __name__ == "__main__":
    main()
