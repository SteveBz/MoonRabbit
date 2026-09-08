import smbus2 # pip3 install smbus2
import bme280 # pip3 install RPi.bme280
import math
import busio # pip3 install adafruit-blinka
import board # pip3 install adafruit-blinka RPI.GPIO

#import adafruit_scd4x #pip3 install adafruit-circuitpython-scd4x
import adafruit_scd30 # pip3 install adafruit-circuitpython-scd30
from urllib.request import urlopen
from class_config_mgt import ConfigManager
from datetime import datetime, timedelta
import time 

from class_geoip_location_provider import LocationProvider
from class_database_mgt import DatabaseManager
# for logging
import sys
import time
import logging

# Set up logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
# import the PyIndi module
try:
    import PyIndi
    from class_pyindi_client import IndiClient
except:
    logger.info (f"Pyindi not installed")
    

import json
#from class_shipLog import logShipping
from class_file_lock import FileLock
class SensorModule:
    PORT = 1
    ADDRESS = 0x76
    ADDRESS2 = 0x77
    # Map reading type to the sensor that produces it
    # Map attribute name to reading type (for building values dict)
    def __init__(self):
        self.bus = smbus2.SMBus(SensorModule.PORT)
        self.device = None
        self.lat = None
        self.long = None
        #print ("__init__")
        self.I2C_status=True


        self.SENSOR_SOURCE_MAP = {
            'co2': 'scd30',
            'humidity': 'bme280',
            'pressure': 'bme280',
            'temperature': 'bme280',
            'wind_speed': 'vantage_pro',
            'wind_direction': 'vantage_pro',
            'rain_rate': 'vantage_pro',
        }
        
        self.ATTR_TO_READING = {
            'co2_val': 'co2',
            'humidity_val': 'humidity',
            'pressure_val': 'pressure',
            'temperature_val': 'temperature',
            'wind_speed': 'wind_speed',
            'wind_direction': 'wind_direction',
            'rain_rate': 'rain_rate',
        }
        self.timer = 0
        self.i2c = None
        self.scd = None
        self.co2_val = None
        self.temperature_val = None
        self.humidity_val = None
        self.pressure_val = None
        self.temp = None
        self.hum = None
        self.co2 = None
        config_manager = ConfigManager("config.json")
        self.lat=config_manager.get_lat()
        self.long=config_manager.get_long()
        self.device=config_manager.get_device_id()
        self.is_registered=config_manager.is_registered()
        #self.bus_address=config_manager.get_bus_address()
        try:
            self.bus_address = int(config_manager.get_bus_address(), 16)  # Convert hex string to int
        except:
            self.bus_address = 0
        bus_address=self.bus_address
        print(bus_address)
        if bus_address == 0:
            bus_address = SensorModule.ADDRESS
            try:
                self.calibration_params = bme280.load_calibration_params(self.bus, SensorModule.ADDRESS)
                config_manager.set_bus_address(bus_address)
            except:
                self.calibration_params = bme280.load_calibration_params(self.bus, SensorModule.ADDRESS2)
                bus_address = SensorModule.ADDRESS2
                #print ("Using ADDRESS2")
                SensorModule.ADDRESS=SensorModule.ADDRESS2
                config_manager.set_bus_address(bus_address)
        else:
            #try:
                self.calibration_params = bme280.load_calibration_params(self.bus, bus_address)
            #except:
            #    self.I2C_status=self.reset_i2c(SensorModule.PORT)
            #    self.calibration_params = bme280.load_calibration_params(self.bus, bus_address)
        
        #print ("calling DatabaseManager")
        #db_manager = DatabaseManager('measurement.db')
        # Commit the changes and close the connection
        #db_manager.conn.commit()
        #db_manager.conn.close()
        # SCD-30 has tempremental I2C with clock stretching, datasheet recommends
        # starting at 50KHz
        self.i2c = busio.I2C(board.SCL, board.SDA) # uses board.SCL and board.SDA
        sample_reading = bme280.sample(self.bus, SensorModule.ADDRESS, self.calibration_params)
        self.temperature_val = sample_reading.temperature
        self.humidity_val = sample_reading.humidity
        self.pressure_val = sample_reading.pressure
        self.scd = adafruit_scd30.SCD30(i2c_bus=self.i2c, ambient_pressure = int(self.pressure_val))
        self.scd.self_calibration_enabled=False
        
        lock = FileLock("SensorModule", lock_dir='locks')  # Use a dedicated directory for lock files
        lock.release_lock(force=True)

    def __del__(self):
        if self.bus is not None:
            self.bus.close()

    def reset_i2c(self, port):
        try:
            bus = SMBus(port)
            bus.close()
            time.sleep(1)  # Allow time for devices to reset
            bus.open(port)
            return True
        except Exception as e:
            print(f"I2C Reset failed: {e}")
            return False
    def get_sensor_readings(self):
        print ("get_sensor_readings")
        
        self.co2_val = self.read_values()
        # Allow for zero value temp or hum in BME280
        if self.humidity_val==0 and self.hum != 0:
            self.humidity_val=self.hum
        if self.temperature_val==0 and self.temp != 0:
            self.temperature_val=self.temp
        #print(1)
        #config_manager = ConfigManager()
        if not self.is_registered:
            config_manager = ConfigManager("config.json")
            self.lat=config_manager.get_lat()
            self.long=config_manager.get_long()
            self.device=config_manager.get_device_id()
            self.is_registered=config_manager.is_registered()
            
        sensor_values = ConfigManager("sensor_values.json")
        sensor_values.get_time_interval_values()
        lock = FileLock("SensorModule", lock_dir='locks')  # Use a dedicated directory for lock files
        lock.acquire_lock(wait=True)
        db_manager = DatabaseManager('measurement.db')
        db_manager.insert_measurement(self.device, 'scd30', self.lat, self.long, 'co2', self.co2_val)
        if "humidity" in self.device_readings:
            source_sensor = self.device_readings["device_name"]   # will be 'vantage_pro' (or whatever you set)
        else:
            source_sensor = 'bme280'
        db_manager.insert_measurement(self.device, source_sensor, self.lat, self.long, 'humidity', self.humidity_val)
        if "pressure" in self.device_readings:
            source_sensor = self.device_readings["device_name"]   # will be 'vantage_pro' (or whatever you set)
        else:
            source_sensor = 'bme280'
        db_manager.insert_measurement(self.device, source_sensor, self.lat, self.long, 'pressure', self.pressure_val)
        if "temperature" in self.device_readings:
            source_sensor = self.device_readings["device_name"]   # will be 'vantage_pro' (or whatever you set)
        else:
            source_sensor = 'bme280'
        db_manager.insert_measurement(self.device, source_sensor, self.lat, self.long, 'temperature', self.temperature_val)
        # Check if self has an attribute named 'wind_direction'
        # Insert wind/rain directly from device_readings (clean keys)
        print("DEBUG: device_readings keys before rain_rate check:", self.device_readings.keys())
        if 'wind_direction' in self.device_readings:
            db_manager.insert_measurement(self.device, self.device_readings["device_name"], self.lat, self.long, 'wind_direction', self.device_readings['wind_direction'])
        if 'wind_speed' in self.device_readings:
            db_manager.insert_measurement(self.device, self.device_readings["device_name"], self.lat, self.long, 'wind_speed', self.device_readings['wind_speed'])
        # Insert wind/rain directly from device_readings (clean keys)
        print("DEBUG: device_readings keys:", self.device_readings.keys())
        rain_rate_val = self.device_readings.get('rain_rate')
        if rain_rate_val is not None:
            db_manager.insert_measurement(self.device, self.device_readings.get('device_name', 'vantage_pro'), self.lat, self.long, 'rain_rate', rain_rate_val)
            print(f"DEBUG: Inserting rain_rate = {rain_rate_val}")
        else:
            print("DEBUG: rain_rate not found or None in device_readings")
        if 'rain_rate' in self.device_readings:
            db_manager.insert_measurement(self.device, self.device_readings["device_name"], self.lat, self.long, 'rain_rate', self.device_readings['rain_rate'])
            print(f"DEBUG: Inserting rain_rate = {self.device_readings['rain_rate']}")

        # Now insert all weather keys (skip 'device_name')
        ignore_keys = {'weather_forecast', 'forecast', 'weather_solar_radiation', 'solar_radiation'}
        duplicate_weather_keys = {
            'weather_wind_direction', 'weather_rain_rate', 'weather_wind_speed',
            'pressure', 'temperature', 'barometer', 'humidity',
            'wind_speed', 'wind_direction', 'rain_rate'   # <-- add these
        }
        weather_data = self.device_readings.copy()  # includes 'device_name' and all weather keys
        sensor_type = weather_data.get('device_name', 'vantage')  # fetch once
        for key, value in weather_data.items():
            if key == 'device_name':
                continue                   # skip device name
            if key in ignore_keys:
                continue                  # not of interest
            if key in duplicate_weather_keys:
                continue                   # skip duplicates; plain versions will be inserted
            
            # Use a fixed sensor type, e.g., 'vantage', or get it from the dict
            db_manager.insert_measurement(self.device, sensor_type, self.lat, self.long, key, value)
        values = {}
        for attr, key in self.ATTR_TO_READING.items():
            val = getattr(self, attr, None)
            if val is not None:
                values[key] = val
        
        config = sensor_values.set_time_interval_values(datetime.now().isoformat(), values)
        
        start_time = datetime.fromisoformat(config["time_intervals"]["min"]["start"])
        end_mins = (start_time + timedelta(minutes=1)).replace(microsecond=0)      
        mean_time =(start_time + timedelta(seconds=30)).replace(microsecond=0)      
        if datetime.now()> end_mins:
            interval="min"
            self.aggregate_interval("sensor_measurement_mins", interval, mean_time, config, db_manager)
            config=sensor_values.remove_interval(interval)
            #logShipping.transfer_to_central_log(db_manager)
        
        start_time = datetime.fromisoformat(config["time_intervals"]["hour"]["start"])
        end_mins = (start_time + timedelta(hours=1)).replace(microsecond=0)      
        mean_time =(start_time + timedelta(minutes=30)).replace(microsecond=0)      
        if datetime.now()> end_mins:
            interval="hour"
            self.aggregate_interval("sensor_measurement_hours", interval, mean_time, config, db_manager)
            config=sensor_values.remove_interval(interval)
            
        start_time = datetime.fromisoformat(config["time_intervals"]["day"]["start"])
        end_mins = (start_time + timedelta(days=1)).replace(microsecond=0)      
        mean_time =(start_time + timedelta(hours=12)).replace(microsecond=0)      
        if datetime.now()> end_mins:
            interval="day"
            self.aggregate_interval("sensor_measurement_days", interval, mean_time, config, db_manager)
            config=sensor_values.remove_interval(interval)

        # Commit the changes and close the connection
        db_manager.conn.commit()
        db_manager.conn.close()
        
        lock.release_lock(force=True)
        retval=(self.temperature_val, self.pressure_val, self.humidity_val, self.co2_val, self.lat, self.long)
            
        # Construct the message as a single formatted string
        log_message = (
            f"{datetime.now().isoformat()} - "
            f"Latitude: {self.lat}, "
            f"Longitude: {self.long}, "
            f"Temperature: {self.temperature_val:.1f} *C, "
            f"Humidity: {self.humidity_val:.1f} %, "
            f"CO2: {int(self.co2_val):,d} ppm, "
            f"Pressure: {int(self.pressure_val):,d} mBars"
        )
        
        # Log the message
        logger.info(log_message)
        
        return retval

    def aggregate_interval(self, table, interval, mean_time, config, db_manager):
        logger.info (f"{interval} aggregate")
        def insert_record_from_array(self, table, sensor_type, reading_type, config):
            sensor_reading_array = config["time_intervals"][interval][reading_type]
            db_manager.insert_aggregate_data(table, mean_time, self.device, sensor_type, self.lat, self.long, reading_type, 
                sum(sensor_reading_array)/len(sensor_reading_array), 
                max(sensor_reading_array), 
                min(sensor_reading_array))
                
        def insert_record_from_value(self, table, sensor_type, reading_type, config):
            sensor_readings = config["time_intervals"][interval]
            #print(sensor_readings)
            db_manager.insert_aggregate_data(table, mean_time, self.device, sensor_type, self.lat, self.long, reading_type, 
                sensor_readings[reading_type]/sensor_readings["count"], 
                0, # max - sort out later 
                0) # min - sort out later

        # NEW dynamic loop
        interval_data = config["time_intervals"][interval]
        
        if interval == "min":
            for reading_type, sensor_type in self.SENSOR_SOURCE_MAP.items():
                if reading_type in interval_data:
                    insert_record_from_array(self, table, sensor_type, reading_type, config)
        else:  # hour or day
            for reading_type, sensor_type in self.SENSOR_SOURCE_MAP.items():
                if reading_type in interval_data:
                    insert_record_from_value(self, table, sensor_type, reading_type, config)
        
    def read_values(self):
        """
        Reads CO2, temperature, and humidity from the SCD30 sensor.
        Applies temperature offset if external reference available.
        Returns True on success, False on failure or timeout.
        """    

         # ---- CO2 reading with timeout ----
        MAX_VALID_CO2 = 5000
        co2_val = 400  # fallback/default
        start_time = time.time()
        timeout = 30  # seconds
        self.device_readings={}
        #self.device_name = 'bme280'   # default fallback
        
        while True:
            # Check for timeout
            if time.time() - start_time > timeout:
                logger.warning("CO2 sensor timeout - using fallback value 400 ppm")
                break
            if self.scd.data_available:
                self.temp=self.scd.temperature
                self.hum=self.scd.relative_humidity
                self.co2=self.scd.CO2

                # check if external reference temperature is available
                if hasattr(self, "temperature_val") and self.temperature_val != 0 and self.temp != 0:
                    self.temperature_offset = self.temp - self.temperature_val
                    self.scd.temperature_offset = self.temperature_offset
                    
                co2_val = self.co2
                if self.co2 < MAX_VALID_CO2:
                        break
            time.sleep(1)
        try:
            indiClient = IndiClient()
        except:
            return self.co2
            
        indiClient.setServer("localhost", 7624)
        
        # Connect to server
        logger.info ("Connecting and waiting 1 sec")
        if not indiClient.connectServer():
            logger.error (
                f"No indiserver running on {indiClient.getHost()}:{indiClient.getPort()} - Try to run"
            )
            logger.info ("  indiserver indi_simulator_telescope indi_simulator_ccd")
            #sys.exit(1)
        
        # Waiting for discover devices
        time.sleep(1)
        
        # Print list of devices. The list is obtained from the wrapper function getDevices as indiClient is an instance
        # of PyIndi.BaseClient and the original C++ array is mapped to a Python List. Each device in this list is an
        # instance of PyIndi.BaseDevice, so we use getDeviceName to print its actual name.
        #print("List of devices")
        deviceList = indiClient.getDevices()
        #for device in deviceList:
        #    print(f"   > {device.getDeviceName()}")
        
        # Print all properties and their associated values.
        #print("List of Device Properties")
        for device in deviceList:
            logger.info(f"-- {device.getDeviceName()}")
            self.device_readings["device_name"] = device.getDeviceName()
        
            if device.getDeviceName() == "Vantage":
                # ---- 1. Connect the device ----
                connect_switch = device.getSwitch("CONNECTION")
                if connect_switch:
                    connect_switch[0].setState(PyIndi.ISS_ON)   # CONNECT
                    connect_switch[1].setState(PyIndi.ISS_OFF)  # DISCONNECT
                    indiClient.sendNewSwitch(connect_switch)
                    logger.info("Sent CONNECT command to Vantage")
                            
                    # ---- Initialise Vantage attributes ----
                    self.vantage_temperature = None
                    self.vantage_humidity = None
                    self.vantage_pressure = None
                    self.rain_rate = None
                    self.wind_speed = None
                    self.wind_direction = None

                    timeout = time.time() + 10   # wait up to 10 seconds

                    required = {'rain_rate', 'wind_speed', 'wind_direction', 'weather_temperature', 'weather_humidity', 'weather_barometer'}
                    collected = set()
                    while time.time() < timeout:
                        
                        genericPropertyList = device.getProperties()
                        # scan for weather properties
                        for prop in genericPropertyList:
                            
                            logger.info (f"   > {prop.getName()} {prop.getTypeAsString()}")
                            if prop.getType() == PyIndi.INDI_NUMBER:
                                for widget in PyIndi.PropertyNumber(prop):
                                    
                                    name = widget.getName().lower()
                                    value = widget.getValue()
                                    # ---- Store weather readings and overwrite BME values ----
                                    if "weather" in name:
                                        print(f"DEBUG: {name} = {value}")   # <-- add this
                                        clean_name = name.replace("weather_", "")   # remove prefix
                                        # Normalise barometer to pressure
                                        if "barometer" in clean_name or "pressure" in clean_name:
                                            clean_name = "pressure"
                                        self.device_readings[clean_name] = value
                                        #self.device_readings[name] = value
                                        self.device_readings["device_name"] = "vantage_pro"
                                        collected.add(name)
    
                                        if "temperature" in name:
                                            self.temperature_val = value   # overwrite BME
                                        elif "humidity" in name:
                                            self.humidity_val = value      # overwrite BME
                                        elif "barometer" in name or "pressure" in name:
                                            self.pressure_val = value      # overwrite BME
                                    # ---- Wind/rain readings ----
                                    if "rain_rate" in name:
                                        self.rain_rate = value
                                        print(f"DEBUG: Rain rate set to {value}")   # <-- add this line
                                        collected.add('rain_rate')
                                    if "wind_speed" in name:
                                        self.wind_speed = value
                                        collected.add('wind_speed')
                                    if "wind_direction" in name:
                                        self.wind_direction = value
                                        collected.add('wind_direction')
                        # ---- Break early if all required readings are collected ----
                        if collected >= required:
                            logger.info(f"All Vantage readings collected: {collected}")
                            break
                        time.sleep(0.5)
                                                    
                # Disconnect from the indiserver
                print("Disconnecting")
                indiClient.disconnectServer()
                print(self.device_readings)
                break
        print(f"DEBUG: Final rain_rate = {self.rain_rate}")
        return co2_val
        
if __name__ == "__main__":
    array = ()
    sensor_reading = SensorModule()
    array = sensor_reading.get_sensor_readings()
