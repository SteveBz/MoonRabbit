import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
import time, math
import pandas as pd # pip3 install pandas
import random
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from class_sqlite_diagnostic import SQLiteDiagnostic
class DatabaseManager:
    def __init__(self, db_file):
        """
        Initialize the DatabaseManager with the given database file.
        :param db_file: The path to the SQLite database file.
        """
        self.db_file = db_file
        self.conn = self.create_connection(db_file)
        self.create_table()
        
    def create_connection(self, db_file):
        """
        Create a database connection to the SQLite database specified by db_file.
        :param db_file: The path to the SQLite database file.
        :return: The database connection object.
        """
        try:
            conn = sqlite3.connect(db_file, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row  # Enable accessing rows by column name
            conn.execute("PRAGMA journal_mode=DELETE")  # Set to WAL mode for better concurrency
            conn.execute("PRAGMA busy_timeout = 10000")  # Increase busy timeout to 10 seconds
            logger.info(f"SQLite version: {sqlite3.version}")
            return conn
        except Error as e:
            logger.error(e)
            return None

    def create_table(self):
        """
        Create tables if they do not exist.
        """
        table_queries = [
            '''
                CREATE TABLE IF NOT EXISTS sensor_measurement (
                    device_id TEXT,
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATETIME,
                    sensor TEXT,
                    latitude REAL,
                    longitude REAL,
                    type TEXT,
                    value REAL,
                    transferred INTEGER DEFAULT 0
                )
                
            ''',
            '''
                CREATE INDEX IF NOT EXISTS reading_index 
                    ON sensor_measurement (date, latitude, longitude, sensor, type)''',
            '''
                CREATE TABLE IF NOT EXISTS sensor_measurement_mins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    date TIMESTAMP NOT NULL,
                    sensor TEXT NOT NULL,
                    type TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    transferred BOOLEAN NOT NULL DEFAULT 0,
                    value REAL NOT NULL,
                    max_value REAL NOT NULL,
                    min_value REAL NOT NULL,
                    UNIQUE(device_id, sensor, type, latitude, longitude, date)
                )
            ''',
            '''
                CREATE INDEX IF NOT EXISTS idx_sensor_measurement_mins 
                    ON sensor_measurement_mins (date)
            ''',
            '''
                CREATE INDEX IF NOT EXISTS idx_sensor_measurement_mins_device_sensor 
                    ON sensor_measurement_mins (device_id, sensor)
            ''',
                
            '''
                CREATE TABLE IF NOT EXISTS sensor_measurement_hours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    date TIMESTAMP NOT NULL,
                    sensor TEXT NOT NULL,
                    type TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    transferred BOOLEAN NOT NULL DEFAULT 0,
                    value REAL NOT NULL,
                    max_value REAL NOT NULL,
                    min_value REAL NOT NULL,
                    UNIQUE(device_id, sensor, type, latitude, longitude, date)
                )
            ''',
            '''
                CREATE INDEX IF NOT EXISTS idx_sensor_measurement_hours 
                    ON sensor_measurement_hours (date)
            ''',
            '''
                CREATE INDEX IF NOT EXISTS idx_sensor_measurement_hours_device_sensor 
                    ON sensor_measurement_hours (device_id, sensor)
            ''',
            '''
                CREATE TABLE IF NOT EXISTS sensor_measurement_days (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER NOT NULL,
                    sensor TEXT NOT NULL,
                    type TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    transferred BOOLEAN NOT NULL DEFAULT 0,
                    date TIMESTAMP NOT NULL,
                    value REAL NOT NULL,
                    max_value REAL NOT NULL,
                    min_value REAL NOT NULL,
                    UNIQUE(device_id, sensor, type, latitude, longitude, date)
                )
            ''',
            '''
                CREATE INDEX IF NOT EXISTS idx_sensor_measurement_days 
                    ON sensor_measurement_days (date)
            ''',
            '''
                CREATE INDEX IF NOT EXISTS idx_sensor_measurement_days_device_sensor 
                    ON sensor_measurement_days (device_id, sensor)
            ''',

        ]

        with self.conn:
            try:
                cursor = self.conn.cursor()
                for query in table_queries:
                    cursor.execute(query)
            except Error as e:
                logger.error(e)

    def select_measurements_by_type(self, sensor_type: str) -> dict:
        """
        Query all rows in the sensor_measurement table with a specific type.
        
        :param sensor_type: The type of sensor to filter by.
        :return: List of rows matching the query.
        """
        select_query = '''
            SELECT * FROM sensor_measurement WHERE type = ? ORDER BY date DESC LIMIT 1
        '''
        rows = self.retry_operation(self._execute_select, select_query, (sensor_type,), retries=5, base_sleep_interval=1, max_sleep_interval=1)
        return rows
        
    def get_latest_measurements_by_type_and_duration(self, sensor_type, duration, max_points):
        """
        Get the latest measurements by type and duration.

        :param sensor_type: The type of sensor to filter by.
        :param duration: The duration to filter by (e.g., '1_hour', '1_day', etc.).
        :param max_points: The maximum number of points to retrieve.
        :return: List of binned results.
        """
        now = datetime.now()
        group_comment=''
        table = 'sensor_measurement'
        if duration == '1_hour' or duration == 'realtime':
            group_comment = ''
            groupPeriod = 'sec'
            start_time = now - timedelta(hours=1)
        elif duration == '1_day':
            group_comment = ''
            groupPeriod = 'min'
            start_time = now - timedelta(days=1)
            table = 'sensor_measurement_mins'
        elif duration == '1_week':
            group_comment = ''
            groupPeriod = 'min'
            start_time = now - timedelta(days=7)
            table = 'sensor_measurement_mins'
        elif duration == '1_month':
            group_comment = ''
            groupPeriod = 'hour'
            start_time = now - timedelta(days=30)
            table = 'sensor_measurement_hours'
        elif duration == '1_year':
            group_comment = ''
            groupPeriod = 'day'
            start_time = now - timedelta(days=365)
            table = 'sensor_measurement_days'
        elif duration == '10_years':
            group_comment = ''
            groupPeriod = 'month'
            start_time = now - timedelta(days=3652)  # Approximately 10 years
        else:
            raise ValueError(f"Invalid duration (Duration = {duration}) specified. Use 'hour', 'day', 'month', or 'year'.")

        select_query = f'''
            SELECT device_id, id, strftime('%Y-%m-%d %H:%M:%S', date) as date, sensor, latitude, longitude, type, value, transferred, 
            strftime('%Y-%m-%d %H:%M:%S', date) as sec, 
            strftime('%Y-%m-%d %H:%M:00', date) as min, 
            strftime('%Y-%m-%d %H:00:00', date) as hour, 
            strftime('%Y-%m-%d 00:00:00', date) as day, 
            strftime('%Y-%m-00 00:00:00', date) as month, 
            AVG(value) as mean_value, MAX(value) as max_value, MIN(value) as min_value
            FROM {table} 
            WHERE type = ? AND date >= ? 
            {group_comment} GROUP BY {groupPeriod}
            ORDER BY date DESC
        '''
        # Use retry_operation for executing the select query
        # Convert start_time to standard string format
        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        rows = self.retry_operation(self._execute_select, select_query, (sensor_type, start_time_str), retries=5, base_sleep_interval=1, max_sleep_interval=1)

        if not rows:
            return []

        # Convert the query results to a DataFrame for easier manipulation
        df = pd.DataFrame(rows, columns=['device_id', 'id', 'date', 'sensor', 'latitude', 'longitude', 'type', 'value', 'transferred', 'sec', 'min', 'hour', 'day', 'month', 'mean_value', 'max_value', 'min_value'])
        
        df['date'] = pd.to_datetime(df['date'])

        # Calculate bin size to limit the number of points to max_points
        total_rows = len(df)
        max_points = int(max_points)
        bin_size = math.ceil(total_rows / max_points)

        binned_results = []
        for i in range(0, total_rows, bin_size):
            bin_slice = df.iloc[i:i + bin_size]

            mean_date = bin_slice['date'].mean().isoformat()
            mean_value = bin_slice['value'].mean()
            max_value = bin_slice['value'].max()
            min_value = bin_slice['value'].min()

            first_row = bin_slice.iloc[0]
            device_id = first_row['device_id']
            sensor = first_row['sensor']
            latitude = first_row['latitude']
            longitude = first_row['longitude']
            transferred = first_row['transferred']
            
            record = (
                str(device_id), None, str(mean_date), str(sensor), float(latitude), float(longitude), float(mean_value), float(max_value), float(min_value), int(transferred)
            )
            #print (record)

            binned_results.append(record)
            
        rows_list = [list(row) for row in binned_results]  # Convert sqlite3.Row to list of lists

        return rows_list


    def select_measurements_by_transferred(self, transferred):
        """
        Retrieve all measurements from the sensor_measurement table based on the transferred status.
        
        :param transferred: The transferred status to filter measurements by (0 or 1).
        :return: List of lists containing measurements.
        """
        select_query = '''
            SELECT device_id, id, date, sensor, latitude, longitude, type, value, transferred
            FROM sensor_measurement WHERE transferred = ? ORDER BY date DESC  LIMIT 50
        '''
        # Use retry_operation to handle potential locking issues
        rows = self.retry_operation(self._execute_select, select_query, (transferred,), retries=5, base_sleep_interval=1, max_sleep_interval=1)
        return rows
    def _execute_select(self, query, params):
        """
        Helper method to execute a select query and fetch all results.
        
        :param query: The SQL query to execute.
        :param params: The parameters for the SQL query.
        :return: List of lists containing the query results.
        """
        print(params)
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                rows = [dict(row) for row in rows]  # Convert rows to dictionaries for easier access
                return rows
        except sqlite3.Error as e:
            logger.error(f"Error executing select query: {e}")
            raise

    def update_measurements_to_transferred(self, id):
        """
        Mark a measurement as transferred in the sensor_measurement table.

        :param id: The id of the measurement to mark as transferred.
        """
        update_query = '''
            UPDATE sensor_measurement SET transferred = 1 WHERE id = ?
        '''
        self.retry_operation(self.conn.cursor().execute, update_query, (id,), retries=2, base_sleep_interval=1, max_sleep_interval=1)

    def insert_measurement(self, device_id, sensor, latitude, longitude, sensor_type, value):
        """
        Insert a new measurement into the sensor_measurement table.

        :param device_id: ID of the device.
        :param sensor: Name of the sensor.
        :param latitude: Latitude of the measurement location.
        :param longitude: Longitude of the measurement location.
        :param sensor_type: Type of sensor measurement.
        :param value: The measured value.
        """
        date_time=datetime.now()
        insert_query = '''
            INSERT INTO sensor_measurement (date, device_id, sensor, latitude, longitude, type, value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.retry_operation(self.conn.cursor().execute, insert_query, [date_time, device_id, sensor, latitude, longitude, sensor_type, value], retries=5, base_sleep_interval=2, max_sleep_interval=10)
        
    def insert_aggregate_data(self, table ,date_time, device_id, sensor, latitude, longitude, sensor_type, value, max_value, min_value):
        """
        Insert a new aggregate measurement into the relevant sensor_measurement_(min/hours/day) table.

        :param table: the table name of the aggregated table.
        :param device_id: ID of the device.
        :param sensor: Name of the sensor.
        :param latitude: Latitude of the measurement location.
        :param longitude: Longitude of the measurement location.
        :param sensor_type: Type of sensor measurement.
        :param value: The measured value.
        """
        date_time=datetime.now()
        # Format date_time to ISO 8601 format
        iso_date = date_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        insert_query = f'''
            INSERT INTO {table} (date, device_id, sensor, latitude, longitude, type, value, max_value, min_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        self.retry_operation(self.conn.cursor().execute, insert_query, [iso_date, device_id, sensor, latitude, longitude, sensor_type, value, max_value, min_value], retries=5, base_sleep_interval=1, max_sleep_interval=10)
        
  
    def retry_operation(self, operation, *args, retries=5, base_sleep_interval=2, max_sleep_interval=10):
        """
        Retry a database operation in case of failure.
    
        :param operation: The database operation to retry.
        :param args: Arguments to pass to the operation.
        :param retries: Number of retry attempts.
        :param base_sleep_interval: Base time to wait between retries.
        :param max_sleep_interval: Maximum time to wait between retries.
        """
        while retries > 0:
            try:
                result = operation(*args)
                self.conn.commit()
                return result  # Return the result for any select operations
            except sqlite3.OperationalError as e:
                logger.error(f"Error:{e}")
                if "database is locked" in str(e):
                    logger.error("Database is locked. Retrying...")
                    retries -= 1
                    if retries > 0:
                        logger.error("Retrying...")
                        #sleep_interval = random.uniform(base_sleep_interval, max_sleep_interval)
                        sleep_interval = min(base_sleep_interval * (2 ** (5 - retries)), max_sleep_interval)
                        time.sleep(sleep_interval)
                    else:
                        logger.error("Maximum retries reached. Operation failed.")
                        diagnostic = SQLiteDiagnostic(self.db_file)
                        diagnostic.run_diagnostics()
                        
                else:
                    raise
            except sqlite3.Error as e:
                logger.error(f"Error:{e}")
                raise

    def close_connection(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
    

if __name__ == "__main__":
    # Example usage of DatabaseManager
    db_file = "measurement.db"
    db_manager = DatabaseManager(db_file)
    
    device_id="GB00001"
    date = datetime.now()
    sensor = "bme280"
    latitude = 0.0
    longitude = 0.0
    sensor_type = "temperature"
    value = 25.0
    db_manager.insert_measurement(device_id, sensor, latitude, longitude, sensor_type, value)

    # Select and print all measurements
    measurements = db_manager.select_measurements_by_transferred(0)
    for measurement in measurements:
        print(measurement)
