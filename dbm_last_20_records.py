import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('measurement.db')  # Replace 'your_database_file.db' with the path to your database file

# Create a cursor object
cursor = conn.cursor()

# Execute the SQL query to get unique device_ids
cursor.execute("SELECT * FROM sensor_measurement ORDER BY date DESC LIMIT 20;")

# Fetch all unique device_ids
records = cursor.fetchall()

# Close the connection
conn.close()

# Print all records
for record in records:
    print(record)

# Or simply:
# print(records)  # This will print the entire list of tuples