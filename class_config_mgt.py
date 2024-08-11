import json
from datetime import datetime, timedelta
import fcntl
class ConfigManager:
    def __init__(self, file='config.json'):
        self.config_file = file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r+') as f:
                fcntl.flock(f, fcntl.LOCK_EX)  # Acquire an exclusive lock
                try:
                    config = json.load(f)
                    fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock
                except json.JSONDecodeError:
                    fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock
                    config = self.create_default_config()
                    self.save_config(config)
                return config
        except FileNotFoundError:
            return self.create_default_config()
            
            
    def save_config(self, config):
        with open(self.config_file, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)  # Acquire an exclusive lock
            json.dump(config, f, indent=4)
            fcntl.flock(f, fcntl.LOCK_UN)  # Release the lock
            
    def create_default_config(self):
        default_config = {
            "device_id": 1,
            "registered": False,
            "status": "00 - Raw",
            "lat": 51.1,
            "long": 0.1,
            "sensor_co2": "scd30",
            "sensor_pressure": "bme280",
            "last_calibration_date": 0,
            "last_calibration_value": 0
        }
        self.save_config(default_config)
        return default_config


    def get_device_id(self):
        return self.config["device_id"]

    def set_device_id(self, device_id):
        self.config["device_id"] = device_id
        self.save_config(self.config)

    def get_lat(self):
        return float(self.config["lat"])

    def set_lat(self, lat):
        self.config["lat"] = round(lat,4)
        self.save_config(self.config)

    def get_long(self):
        return float(self.config["long"])

    def set_long(self, long):
        self.config["long"] = round(long,4)
        self.save_config(self.config)
    def get_time_interval_values(self, interval):
        if "time_intervals" not in self.config:
            self.config["time_intervals"] = {
                "month": {
                    "start":datetime.now().isoformat(),
                    "co2": 0,
                    "temperature": 0,
                    "humidity": 0,
                    "pressure": 0,
                    "count": 0
                },
                "min": {
                    "start":datetime.now().isoformat(),
                    "co2": [],
                    "temperature": [],
                    "humidity": [],
                    "pressure": [],
                },
                "hour": {
                    "start":datetime.now().isoformat(),
                    "co2": 0,
                    "temperature": 0,
                    "humidity": 0,
                    "pressure": 0,
                    "count": 0
                },
                "day": {
                    "start":datetime.now().isoformat(),
                    "co2": 0,
                    "temperature": 0,
                    "humidity": 0,
                    "pressure": 0,
                    "count": 0
                }
            }
            self.save_config(self.config)
        
        if interval in self.config["time_intervals"]:
            return self.config["time_intervals"][interval]
        else:
            raise KeyError(f"Invalid interval '{interval}' for time intervals")

    def remove_interval(self, interval):
        del self.config["time_intervals"][interval]
        if interval == "min":
            self.config["time_intervals"]["min"] = {
                    "start":datetime.now().isoformat(),
                    "co2": [],
                    "temperature": [],
                    "humidity": [],
                    "pressure": [],
                }
        else:
            self.config["time_intervals"][interval]= {
                "start":datetime.now().isoformat(),
                "co2": 0,
                "temperature": 0,
                "humidity": 0,
                "pressure": 0,
                "count":0
            }
        self.save_config(self.config)
        return self.config
            
    def set_time_interval_values(self, date_time, sensor_value_dict):
        if "min" not in self.config["time_intervals"]:
            self.config["time_intervals"]["min"] = {
                    "start":date_time,
                    "co2": [],
                    "temperature": [],
                    "humidity": [],
                    "pressure": [],
                }
        if "hour" not in self.config["time_intervals"]:
            self.config["time_intervals"]["hour"]: {
                "start":date_time,
                "co2": 0,
                "temperature": 0,
                "humidity": 0,
                "pressure": 0,
                "count":0
            }
        if "day" not in self.config["time_intervals"]:
            self.config["time_intervals"]["day"]: {
                "start":date_time,
                "co2": 0,
                "temperature": 0,
                "humidity": 0,
                "pressure": 0,
                "count":0
            }
        if "month" not in self.config["time_intervals"]:
            self.config["time_intervals"]["month"]: {
                "start":date_time,
                "co2": 0,
                "temperature": 0,
                "humidity": 0,
                "pressure": 0,
                "count":0
            }

        for interval in self.config["time_intervals"]:
        
            match interval:
                case "min":
                    self.config["time_intervals"][interval]["co2"].append(sensor_value_dict["co2"])
                    self.config["time_intervals"][interval]["temperature"].append(sensor_value_dict["temperature"])
                    self.config["time_intervals"][interval]["humidity"].append(sensor_value_dict["humidity"])
                    self.config["time_intervals"][interval]["pressure"].append(sensor_value_dict["pressure"])
                case _:
                    self.config["time_intervals"][interval]["co2"] += sensor_value_dict["co2"]
                    self.config["time_intervals"][interval]["temperature"] += sensor_value_dict["temperature"]
                    self.config["time_intervals"][interval]["humidity"] += sensor_value_dict["humidity"]
                    self.config["time_intervals"][interval]["pressure"] += sensor_value_dict["pressure"]
                    self.config["time_intervals"][interval]["count"] += 1
        self.save_config(self.config)
        return self.config


# Usage example:
if __name__ == "__main__":
    config_manager = ConfigManager()
    
    print("\nTest 10 return device ID:")
    print("Device ID:", config_manager.get_device_id())
    
    print("\nTest 20 return Latitude:")
    print("Latitude:", config_manager.get_lat())
    
    print("\nTest 30 return Longitude:")
    print("Longitude:", config_manager.get_long())
    
    print("\nTest 30 return minute subtotals:")
    # Set and get sensor values for different time intervals
    config_manager.set_time_interval_values(datetime.now(), {"co2": 420} )
    print("Minutes:", config_manager.get_time_interval_values("min"))

    print("\nTest 40 return invalid time period - ERROR:")
    # Try to get an invalid time interval value
    try:
        print("Invalid key:", config_manager.get_time_interval_values("weeks"))
    except KeyError as e:
        print("Error:", e)
