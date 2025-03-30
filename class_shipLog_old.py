import requests  # pip3 install requests
from datetime import datetime
import time
from class_database_mgt import DatabaseManager

from class_config_mgt import ConfigManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class logShipping:

    @staticmethod
    def transfer_to_central_log(db_manager):
        # Connect to the local SQLite database
        #db_manager = DatabaseManager('measurement.db')

        config_manager = ConfigManager("config.json")
        
        if not config_manager.is_registered():
            url = 'http://www.carbonactive.org/cgi-bin/device_register.py'
            
            try:
                response = requests.get(url)
                response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
                
                # You can now process the response if needed
                device_id = response.json()  # Or response.text if it's not JSON
                
                # Do something with device_data
                print(device_id)
                config_manager.set_device_id(device_id)
                config_manager.set_registered()
                db_manager.update_device_id(device_id)
                
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred: {http_err}")
            except Exception as err:
                print(f"An error occurred: {err}")
          
        # Query local database for new entries
        new_entries = db_manager.select_measurements_by_transferred(0)
        logger.info(f"Number of new entries to transfer: {len(new_entries)}")
        
        # Send new entries to central log
        for entry in new_entries:
            #print(entry)
            data = {
                'device_id': entry['device_id'],
                'date': entry['date'],
                'sensor': entry['sensor'],
                'latitude': entry['latitude'],
                'longitude': entry['longitude'],
                'type': entry['type'],
                'value': entry['value']
            }
            url = 'http://www.carbonactive.org/cgi-bin/sensor_data_logger.py'
            try:
                response = requests.post(url, json=data)
                #logger.info(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    #logger.info(f"Entry ID {entry['id']} and value {entry['value']} transferred successfully")
                    try:
                        # Mark the transferred entries in the local database
                        db_manager.update_measurements_to_transferred(entry['id'])
                    except Exception as e:
                        logger.error(f"Error updating transfer column {e}")
                        logger.error(f"Transferring data: {data}")
                    db_manager.conn.commit()
                    # logger.info("Data transferred successfully to central log")
                else:
                    logger.error("Failed to transfer data to central log:", response.text, url)
                    logger.error(f"Transferring data: {data}")
                    break  # Exit loop on failure to transfer
            except requests.exceptions.RequestException as e:
                logger.error("Exception occurred during data transfer:", e)
                logger.error("Server might be down. Retrying later ...")
                break  # Exit loop on network issue

        # Close connections
        #db_manager.conn.close()


# Call the function to start transferring entries to the central log
if __name__ == "__main__":
    # Connect to the local SQLite database
    db_manager = DatabaseManager('measurement.db')
    try:
        while True:
            logShipping.transfer_to_central_log(db_manager)
            logger.info("Waiting ....")
            time.sleep(300)
    finally:
        # Close connections
        db_manager.conn.close()
