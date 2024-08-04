import requests  # pip3 install requests
from datetime import datetime
import time
from class_database_mgt import DatabaseManager

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from class_file_lock import FileLock

class logShipping:

    @staticmethod
    def transfer_to_central_log(db_manager):
        # Connect to the local SQLite database
        #db_manager = DatabaseManager('measurement.db')

        # Query local database for new entries
        new_entries = db_manager.select_measurements_by_transferred(0)
        logger.info(f"Number of new entries to transfer: {len(new_entries)}")
        
        # Send new entries to central log
        lock = FileLock("logShipping", lock_dir='locks')  # Use a dedicated directory for lock files
        locked_or_waiting=lock.get_lock_status()
        if locked_or_waiting:
            print(f"locked files are {lock.get_lock_files}")
            return
        if not lock.acquire_lock(wait=False):
            return false
        for entry in new_entries:
            logger.info(entry)
            
            locked_or_waiting=lock.get_lock_status()
            if locked_or_waiting:
                print(f"locked files are {lock.get_lock_files}")
                lock.release_lock(force=True)
                return
            data = {
                'device_id': entry['device_id'],
                'date': entry['date'],
                'sensor': entry['sensor'],
                'latitude': entry['latitude'],
                'longitude': entry['longitude'],
                'type': entry['type'],
                'value': entry['value']
            }
            url = 'http://192.168.1.162:5000/sensor_data'
            try:
                response = requests.post(url, json=data)
                logger.info(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"Entry ID {entry['id']} and value {entry['value']} transferred successfully")
                    try:
                        # Mark the transferred entries in the local database
                        db_manager.update_measurements_to_transferred(entry['id'])
                    except Exception as e:
                        logger.error(f"Error updating transfer column {e}")
                        logger.error(f"Transferring data: {data}")
                    db_manager.conn.commit()
                    logger.info("Data transferred successfully to central log")
                else:
                    logger.error(f"Failed to transfer data to central log: {response.text}, url = {url}")
                    logger.error(f"Transferring data: {data}")
                    lock.release_lock(force=True)
                    break  # Exit loop on failure to transfer
            except requests.exceptions.RequestException as e:
                logger.error(f"Exception occurred during data transfer: {e}")
                logger.error("Server might be down. Retrying later ...")
                lock.release_lock(force=True)
                break  # Exit loop on network issue

            print("Next loop")
        lock.release_lock(force=True)
        print("Exit loop")
        # Close connections
        #db_manager.conn.close()


# Call the function to start transferring entries to the central log
if __name__ == "__main__":
    # Connect to the local SQLite database
    
    lock = FileLock("logShipping", lock_dir='locks')  # Use a dedicated directory for lock files
    lock.release_lock(force=True)
    db_manager = DatabaseManager('measurement.db')
    try:
        while True:
            logShipping.transfer_to_central_log(db_manager)
            logger.info("Waiting ....")
            time.sleep(15)
    finally:
        # Close connections
        db_manager.conn.close()