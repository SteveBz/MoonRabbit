from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from class_sensor_module import SensorModule
from class_database_mgt import DatabaseManager
from class_config_mgt import ConfigManager
import subprocess
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5000"}})

# ==============================================================
# NEW: Sensor metadata configuration for the generic v2 API
# ==============================================================
SENSOR_METADATA = {
    "temperature": {"unit": "°C", "min": -10, "max": 50, "reference": 23, "color": "#B22222"},
    "humidity":    {"unit": "%",   "min": 0,   "max": 100, "reference": 50, "color": "#00008B"},
    "pressure":    {"unit": "hPa", "min": 850, "max": 1100, "reference": 1000, "color": "#FF4500"},
    "co2":         {"unit": "ppm", "min": 200, "max": 1000, "reference": 420, "color": "#008080"},
    "sky_temperature": {"unit": "°C", "min": -30, "max": 50, "reference": 0, "color": "#8A2BE2"},
    "rain_rate":   {"unit": "mm/h", "min": 0, "max": 50, "reference": 0, "color": "#1E90FF"},
    "wind_speed":  {"unit": "m/s", "min": 0, "max": 30, "reference": 0, "color": "#32CD32"},
    "wind_direction": {"unit": "°", "min": 0, "max": 360, "reference": 0, "color": "#FFD700"},
    "rain":        {"unit": "mm", "min": 0, "max": 500, "reference": 0, "color": "#00BFFF"}
}

def get_active_sensor_types():
    db = DatabaseManager('measurement.db')
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT DISTINCT type FROM sensor_measurement")
        rows = cursor.fetchall()
        types = [row[0] for row in rows]
        logger.info(f"Active sensor types found: {types}")
        return types
    except Exception as e:
        logger.error(f"Error fetching sensor types: {e}")
        return []
    finally:
        db.conn.close()

def get_sensor_metadata_for_type(sensor_type):
    default = {"unit": "", "min": 0, "max": 100, "reference": 0, "color": "#1f77b4"}
    meta = SENSOR_METADATA.get(sensor_type, default).copy()
    meta["name"] = sensor_type
    return meta

# ==============================================================
# NEW: V2 API ENDPOINTS
# ==============================================================
@app.route('/v2/sensorMetadata', methods=['GET'])
def v2_sensor_metadata():
    logger.info("v2_sensorMetadata called")
    types = get_active_sensor_types()
    result = [get_sensor_metadata_for_type(t) for t in types]
    logger.info(f"v2_sensorMetadata returning {len(result)} sensor types")
    return jsonify(result)

@app.route('/v2/sensorReadings', methods=['GET'])
def v2_sensor_readings():
    logger.info("v2_sensorReadings called")
    db = DatabaseManager('measurement.db')
    types = get_active_sensor_types()
    readings = []
    for sensor_type in types:
        try:
            latest = db.select_measurements_by_type(sensor_type)
            if latest:
                record = latest[0]
                readings.append({
                    "name": sensor_type,
                    "value": record["value"],
                    "unit": SENSOR_METADATA.get(sensor_type, {}).get("unit", ""),
                    "min": SENSOR_METADATA.get(sensor_type, {}).get("min", 0),
                    "max": SENSOR_METADATA.get(sensor_type, {}).get("max", 100),
                    "reference": SENSOR_METADATA.get(sensor_type, {}).get("reference", 0),
                    "color": SENSOR_METADATA.get(sensor_type, {}).get("color", "#1f77b4")
                })
        except Exception as e:
            logger.error(f"Error reading {sensor_type}: {e}")
    db.conn.close()
    logger.info(f"v2_sensorReadings returning {len(readings)} readings")
    return jsonify(readings)

@app.route('/v2/refreshHistory', methods=['GET'])
def v2_refresh_history():
    max_points = request.args.get('maxPoints', default=360, type=int)
    duration = request.args.get('duration', default='realtime', type=str)
    logger.info(f"v2_refreshHistory called with maxPoints={max_points}, duration={duration}")
    db = DatabaseManager('measurement.db')
    types = get_active_sensor_types()
    history = {}
    for sensor_type in types:
        try:
            records = db.get_latest_measurements_by_type_and_duration(sensor_type, duration, max_points)
            data_points = []
            for rec in records:
                if isinstance(rec, dict):
                    ts = rec.get('date')
                    val = rec.get('value')
                else:
                    # fallback tuple – adjust indices if needed
                    ts = rec[2] if len(rec) > 2 else None
                    val = rec[7] if len(rec) > 7 else None
                if ts and val is not None:
                    if isinstance(ts, datetime):
                        ts = ts.isoformat()
                    data_points.append([ts, val])
            history[sensor_type] = data_points
        except Exception as e:
            logger.error(f"History error for {sensor_type}: {e}")
            history[sensor_type] = []
    db.conn.close()
    logger.info(f"v2_refreshHistory returning data for {len(history)} sensor types")
    return jsonify(history)

# ==============================================================
# LEGACY ROUTES – with added trace logging
# ==============================================================

@app.route("/")
def hello_world():
    logger.info("Legacy root (/) called – serving index.html")
    return render_template("index.html")

@app.route('/refreshHistory')
def refresh_history():
    max_points = request.args.get('maxPoints')
    duration = request.args.get('duration')
    logger.info(f"LEGACY refreshHistory called – maxPoints={max_points}, duration={duration}")
    db_manager = DatabaseManager('measurement.db')
    sensor_types = ['temperature', 'pressure', 'humidity', 'co2', 'sky_temperature', 'rain_rate', 'wind_speed', 'wind_direction', 'rain']
    historical_data = {}
    for sensor_type in sensor_types:
        try:
            historical_data[sensor_type] = db_manager.get_latest_measurements_by_type_and_duration(sensor_type, duration, max_points)
        except Exception as e:
            logger.error(f"LEGACY refreshHistory: error fetching {sensor_type}: {e}")
            historical_data[sensor_type] = []
    db_manager.conn.close()
    logger.info(f"LEGACY refreshHistory returning {len(historical_data)} sensor types")
    return jsonify(historical_data)

@app.route('/sensorReadings')
def get_sensor_data():
    logger.info("LEGACY sensorReadings called")
    db_manager = DatabaseManager('measurement.db')
    latest_entries = {}
    sensor_types = ['temperature', 'pressure', 'humidity', 'co2']
    conf = ConfigManager("config.json")
    latitude = conf.get_lat()
    longitude = conf.get_long()
    for sensor_type in sensor_types:
        try:
            [latest_entry] = db_manager.select_measurements_by_type(sensor_type)
            if latest_entry:
                latest_entries[sensor_type.lower()] = {
                    "date": latest_entry["date"],
                    "sensor": latest_entry["sensor"],
                    "latitude": latest_entry["latitude"],
                    "longitude": latest_entry["longitude"],
                    "type": latest_entry["type"],
                    "value": latest_entry["value"]
                }
        except Exception as e:
            logger.error(f"LEGACY sensorReadings: error reading {sensor_type}: {e}")
    db_manager.conn.close()
    if not latest_entries:
        logger.warning("LEGACY sensorReadings: No sensor data found")
        return jsonify({"status": "Error", "message": "No sensor data found"})
    retVal = {
        "status": "OK",
        "temperature": latest_entries["temperature"]["value"],
        "pressure": latest_entries["pressure"]["value"],
        "humidity": latest_entries["humidity"]["value"],
        "co2": latest_entries["co2"]["value"],
        "latitude": latest_entries["temperature"]["latitude"],
        "longitude": latest_entries["temperature"]["longitude"]
    }
    logger.info(f"LEGACY sensorReadings returning OK with temp={retVal['temperature']}, pressure={retVal['pressure']}, etc.")
    return jsonify(retVal)

@app.route('/update_sw', methods=['POST'])
def update_sw():
    logger.info("LEGACY update_sw called")
    print("Updating Software")
    git_pull_cmd = "git pull"
    install_cmd = "sh install.sh"
    reboot_cmd = "/usr/bin/sudo /sbin/reboot"
    try:
        subprocess.run(git_pull_cmd, shell=True, check=True)
        subprocess.run(install_cmd, shell=True, check=True)
        subprocess.run(reboot_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"LEGACY update_sw error: {e}")
        print(f"Error: Command '{e.cmd}' returned non-zero exit status {e.returncode}")
    return 'Software update action initiated'

@app.route('/reboot', methods=['POST'])
def reboot():
    logger.info("LEGACY reboot called")
    print("Rebooting sensor")
    command = "/usr/bin/sudo /sbin/reboot"
    subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    return 'Reboot action initiated'

@app.route('/shutdown', methods=['POST'])
def shutdown():
    logger.info("LEGACY shutdown called")
    print("Shutdown sensor")
    command = "/usr/bin/sudo /sbin/shutdown now"
    subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    return 'Shutdown action initiated'

@app.route('/updateLatitude', methods=['POST'])
def update_latitude():
    logger.info("LEGACY updateLatitude called")
    if request.method == 'POST':
        data = request.get_json()
        latitude = data.get('latitude')
        conf = ConfigManager()
        conf.set_lat(float(latitude))
        logger.info(f"LEGACY updateLatitude set to {latitude}")
        return jsonify({'message': 'Latitude updated successfully'}), 200
    else:
        return jsonify({'error': 'Only POST requests are allowed'}), 405

@app.route('/updateLongitude', methods=['POST'])
def update_longitude():
    logger.info("LEGACY updateLongitude called")
    if request.method == 'POST':
        data = request.get_json()
        longitude = data.get('longitude')
        conf = ConfigManager()
        conf.set_long(float(longitude))
        logger.info(f"LEGACY updateLongitude set to {longitude}")
        return jsonify({'message': 'Longitude updated successfully'}), 200
    else:
        return jsonify({'error': 'Only POST requests are allowed'}), 405

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
