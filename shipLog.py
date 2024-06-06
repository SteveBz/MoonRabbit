import requests # pip3 install requests
from datetime import datetime
import time
from class_database_mgt import DatabaseManager

class logShipping():
  def transfer_to_central_log():
      # Connect to the local SQLite database
      db_manager = DatabaseManager('measurement.db')
  
      # Query local database for new entries
      new_entries=db_manager.select_measurements_by_transferred(0)
      print (len(new_entries))
      # Send new entries to central log
      for entry in new_entries:
          data = {
              'device_id': entry[0],
              'date': entry[2],
              'sensor': entry[3],
              'latitude': entry[4],
              'longitude': entry[5],
              'type': entry[6],
              'value': entry[7]
          }
          print(data)
          url='http://192.168.1.162:5000/sensor_data'
          try:
            response = requests.post(url, json=data)
            print(response.status_code)
            if response.status_code == 200:
                print (f"entry [1] = {entry[1]}, [7] = {entry[7]}")
                try:
                # Mark the transferred entries in the local database
                  db_manager.update_measurements_to_transferred(entry[1])
                except Exception as e:
                    print (f"Error updating transfer column {e}")
                db_manager.conn.commit()
                print("Data transferred successfully to central log")
            else:
                print("Failed to transfer data to central log:", response.text, url)
          except requests.exceptions.RequestException as e:
            print("Exception occurred:", e)
            print("Server might be down. Retrying later ...")
            #time.sleep(30)
            break
      # Close connections       
      db_manager.conn.close()

# Call the function to start transferring entries to the central log
if __name__ == "__main__":
      while True:
           logShipping.transfer_to_central_log()
           print("Waiting ....")
           time.sleep(300)
