import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('measurement.db')  # Replace 'your_database_file.db' with the path to your database file

# Create a cursor object
cursor = conn.cursor()

# Execute the SQL query to get unique device_id, latitude, and longitude combinations
cursor.execute("SELECT DISTINCT device_id, latitude, longitude FROM sensor_measurement")

# Fetch all unique device_id, latitude, and longitude combinations
unique_device_lat_long = cursor.fetchall()

# Close the connection
conn.close()

# Print the unique device_id, latitude, and longitude combinations
for device_id, lat, long in unique_device_lat_long:
    print(f"Device ID: {device_id}, Latitude: {lat}, Longitude: {long}")

