import sqlite3

def print_db_schema():
    # Connect to the SQLite database
    conn = sqlite3.connect('measurement.db')
    cursor = conn.cursor()

    # Get a list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Print the schema for each table
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")
        print("Columns:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  {column[1]}  {column[2]}")
        print("\n")

    # Close the connection
    conn.close()

# Call the function to print the database schema
print_db_schema()
