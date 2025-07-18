import sqlite3
import csv
import os
from datetime import datetime
from class_database_mgt import DatabaseManager
from class_config_mgt import ConfigManager
import logging
from sqlalchemy import create_engine
import pandas as pd

from class_file_lock import FileLock

# Set up logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_PATH = '/home/pi/MoonRabbit/measurement.db'  # Full path to your database
OUTPUT_DIR = '/home/pi/MoonRabbit/exports'  # Directory for CSV files

def export_data():
    """Export data to CSV files"""
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    tables_to_export = {
        'sensor_measurement': 'raw_data',
    #    'sensor_measurement_days': 'daily_summaries',
    #    'sensor_measurement_hours': 'hourly_summaries',
    #    'sensor_measurement_mins': 'minute_summaries'
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    csv_path = os.path.join(OUTPUT_DIR, f"{timestamp}_raw_data.csv")
    print(f"Exporting rows from sensor_measurement to {os.path.basename(csv_path)}")
        
    # Connect to the local SQLite database
    # db_manager = DatabaseManager(DATABASE_PATH)
    # Create SQLAlchemy engine
    engine = create_engine(f'sqlite:///{DATABASE_PATH}')
    # rows=db_manager.select_measurements_all()
    chunk_size = 1000  # Adjust based on available memory
    offset = 0
    first_chunk = True                   # For header handling
    
    total_rows = 0
    
    query = "SELECT * FROM sensor_measurement"
    for df_chunk in pd.read_sql(query, engine, chunksize=1000):
        # Process each chunk
        #print(f"Processing rows {offset + 1} to {offset + len(df_chunk)}")
        
        #offset += chunk_size
        
        # Get actual number of rows in this chunk
        chunk_rows = len(df_chunk)
        print(f"Processing rows {total_rows + 1} to {total_rows + chunk_rows}")
        total_rows += chunk_rows
        # {insert processong here
    
    #print(f"Exporting {len(rows)} rows from sensor_measurement to {os.path.basename(csv_path)}")
    #exit()
    #if not rows:
    #    print(f"Warning: No data found in {table}")
    #    db_manager.close_connection()

    # Convert to list of tuples (like your original code)
        #rows = [tuple(row) for row in df_chunk.to_dict('records')]
        
        # Write to CSV (append after first chunk)
        #with open(csv_path, 'a' if not first_chunk else 'w', newline='') as f:
        #    writer = csv.writer(f)
        #    if first_chunk:
        #        writer.writerow(df_chunk.columns)  # Header (only once)
        #        first_chunk = False
        #    writer.writerows(rows)


        with open(csv_path, 'a' if not first_chunk else 'w', newline='') as f:
            # Convert DataFrame directly to CSV (more efficient than manual conversion)
            df_chunk.to_csv(f, header=first_chunk, index=False)
            first_chunk = False
            
    print(f"Exported {offset} rows from sensor_measurement to {os.path.basename(csv_path)}")
    lock.release_lock(force=True)  # Single guaranteed release
    #db_manager.close_connection()

if __name__ == "__main__":
    # Make sure lock file is released before starting
    print(1)
    lock = FileLock("csv_export", lock_dir='locks')  # Use a dedicated directory for lock files
    print(3)
    locked_or_waiting=lock.get_lock_status()
    
    print(5 )
    if locked_or_waiting:
        print(f"locked files are {lock.get_lock_files}")
        # return
        exit()
        
    # New version (fixed):
    if not lock.acquire_lock(wait=False):
        logger.info("Skipping transfer - another process holds the lock")
        # return False  # <- Proper Python boolean
        exit()

    print(f"Starting export from {DATABASE_PATH}")
    export_data()
    print("Export process completed")
