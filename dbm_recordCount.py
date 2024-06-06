import sqlite3

def count_records_status(table_name):
    # Connect to the SQLite database
    conn = sqlite3.connect('measurement.db')
    cursor = conn.cursor()

    # Define the SQL query to count transferred records
    transferred_count_query = f"SELECT COUNT(*) FROM {table_name} WHERE transferred = 1"

    # Execute the SQL query to count transferred records
    cursor.execute(transferred_count_query)
    transferred_count_result = cursor.fetchone()
    transferred_count = transferred_count_result[0]

    # Define the SQL query to count not yet transferred records
    not_transferred_count_query = f"SELECT COUNT(*) FROM {table_name} WHERE transferred = 0"

    # Execute the SQL query to count not yet transferred records
    cursor.execute(not_transferred_count_query)
    not_transferred_count_result = cursor.fetchone()
    not_transferred_count = not_transferred_count_result[0]

    # Close the connection
    conn.close()

    return transferred_count, not_transferred_count

# Example usage:
table_name = 'sensor_measurement'
transferred_count, not_transferred_count = count_records_status(table_name)
print(f"Transferred records: {transferred_count}")
print(f"Not yet transferred records: {not_transferred_count}")
