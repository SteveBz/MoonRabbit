from flask import Flask, render_template, jsonify, request # pip3 install flask
from flask_cors import CORS # pip3 install flask-cors
from class_sensor_module import SensorModule
from class_database_mgt import DatabaseManager
from class_config_mgt import ConfigManager
import subprocess
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#import sqlite3
#from sqlite3 import Error

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://192.168.1.131:5000"}})

@app.route("/")
def hello_world():
    return render_template("index.html") 
  
@app.route('/refreshHistory')
def refresh_history():
    # Retrieve the value of maxPoints from the request query parameters
    max_points = request.args.get('maxPoints')
    duration = request.args.get('duration')
    # Use max_points as needed, for example, to limit the number of data points fetched from the database
    
    # Your logic to refresh historical data goes here
    # Perform any necessary operations to refresh the history (e.g., reinterrogate the database)
    # You can put the logic here to reinterrogate the database
    # For simplicity, let's just return a success message
    # Initialize the DatabaseManager class.
    db_manager = DatabaseManager('measurement.db')
    
    # Fetch the latest historical data for each sensor type from the database
    sensor_types = ['temperature', 'pressure', 'humidity', 'co2']
    historical_data = {}
    for sensor_type in sensor_types:
        historical_data[sensor_type] = db_manager.get_latest_measurements_by_type_and_duration(sensor_type, duration, max_points)
    
    # Close the connection
    db_manager.conn.close()
    # print(historical_data)
    return jsonify(historical_data)
    #return jsonify({'message': 'History refreshed successfully'}), 200

@app.route('/sensorReadings')
def get_sensor_data():
    
    # Initializes the DatabaseManager class.
    db_manager = DatabaseManager('measurement.db')
    
    # Fetch the latest entry for each sensor type from the database
    latest_entries = {}
    sensor_types = ['temperature', 'pressure', 'humidity', 'co2']
    for sensor_type in sensor_types:
        
        [latest_entry] = db_manager.select_measurements_by_type(sensor_type)
        #print (f"latest_entry ({type(latest_entry)}) {latest_entry}")
        #print(latest_entry.keys())
        # Check if the length of latest_entry is even

        conf = ConfigManager()
        latitude=conf.get_lat()
        longitude=conf.get_long()
        if latest_entry:
            #id, device, date, sensor, _, _, _, value, _ = latest_entry[0]
            latest_entries[sensor_type.lower()] = {
                "date": latest_entry["date"],
                "sensor": latest_entry["sensor"],
                "latitude": latest_entry["latitude"],
                "longitude": latest_entry["longitude"],
                "type": latest_entry["type"],
                "value": latest_entry["value"]
            }
        #print (latest_entry[0])
    # Close the connection
    db_manager.conn.close()
    # If no data found for any sensor type, return error response
    if not latest_entries:
        print(jsonify({"status": "Error", "message": "No sensor data found"}))
        return jsonify({"status": "Error", "message": "No sensor data found"})
    #logger.info (latest_entries)
    retVal={
            "status": "OK",
            "temperature": latest_entries["temperature"]["value"],
            "pressure": latest_entries["pressure"]["value"],
            "humidity": latest_entries["humidity"]["value"],
            "co2": latest_entries["co2"]["value"],
            "latitude": latest_entries["temperature"]["latitude"],
            "longitude": latest_entries["temperature"]["longitude"]
            
        }
    logger.info(retVal)
    return jsonify(retVal)
        
    
@app.route('/reboot', methods=['POST'])
def reboot():
    # Perform any necessary actions to initiate a reboot
    print("Rebooting sensor")
    command = "/usr/bin/sudo /sbin/reboot"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)
    # Return message
    return 'Reboot action initiated'

@app.route('/shutdown', methods=['POST'])
def shutdown():
    # Perform any necessary actions to initiate a reboot
    print("Shutdown sensor")
    command = "/usr/bin/sudo /sbin/shutdown now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)
    # Return message
    return 'Shutdown action initiated'

    
@app.route('/updateLatitude', methods=['POST'])
def update_latitude():
    if request.method == 'POST':
        data = request.get_json()  # Get the JSON data from the request
        latitude = data.get('latitude')  # Extract the latitude value
        # Perform any necessary operations with the latitude data
        conf = ConfigManager()
        conf.set_lat(float(latitude))
        # Return response
        return jsonify({'message': 'Latitude updated successfully'}), 200
    else:
        return jsonify({'error': 'Only POST requests are allowed'}), 405

  
  
@app.route('/updateLongitude', methods=['POST'])
def update_longitude():
    if request.method == 'POST':
        data = request.get_json()  # Get the JSON data from the request
        longitude = data.get('longitude')  # Extract the longitude value
        conf = ConfigManager()
        conf.set_long(float(longitude))
        # Return response
        return jsonify({'message': 'Longitude updated successfully'}), 200
    else:
        return jsonify({'error': 'Only POST requests are allowed'}), 405

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
