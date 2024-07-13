import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('measurement.db')  # Replace 'your_database_file.db' with the path to your database file

# Create a cursor object
cursor = conn.cursor()

# Execute the SQL query to get unique device_ids
cursor.execute("SELECT DISTINCT device_id FROM sensor_measurement")

# Fetch all unique device_ids
unique_device_ids = cursor.fetchall()

# Close the connection
conn.close()

# Print the unique device_ids
print([device_id[0] for device_id in unique_device_ids])
