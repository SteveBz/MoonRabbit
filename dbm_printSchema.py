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

        # Print the indices for the table
        print("Indices:")
        cursor.execute(f"PRAGMA index_list({table_name})")
        indices = cursor.fetchall()
        for index in indices:
            index_name = index[1]
            unique = "UNIQUE" if index[2] else ""
            print(f"  {index_name} {unique}")

            # Get the columns that the index applies to
            cursor.execute(f"PRAGMA index_info({index_name})")
            index_info = cursor.fetchall()
            index_columns = [info[2] for info in index_info]
            print(f"    Columns: {', '.join(index_columns)}")

        # Print the primary key
        print("Primary Key:")
        pk_columns = [col[1] for col in columns if col[5]]  # col[5] is the primary key flag
        if pk_columns:
            print(f"  {', '.join(pk_columns)}")
        else:
            print("  No primary key defined")

        print("\n")

    # Close the connection
    conn.close()

# Call the function to print the database schema
print_db_schema()
