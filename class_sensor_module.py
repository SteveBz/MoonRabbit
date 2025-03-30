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
    I2C_status=True
       
    def __init__(self):
        #print ("__init__")
        config_manager = ConfigManager("config.json")
        self.lat=config_manager.get_lat()
        self.long=config_manager.get_long()
        self.device=config_manager.get_device_id()
        self.is_registered=config_manager.is_registered()
        self.bus_address=config_manager.get_bus_address()
        bus_address=self.bus_address
        self.bus = smbus2.SMBus(SensorModule.PORT)
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
            try:
                self.calibration_params = bme280.load_calibration_params(self.bus, bus_address)
            except:
                self.I2C_status=self.reset_i2c(SensorModule.PORT)
        self.timer = 0
        self.i2c = None
        self.scd = None
        self.co2_val = None
        self.lat = None
        self.long = None
        self.temperature_val = None
        self.humidity_val = None
        self.pressure_val = None
        self.device = None
        self.temp = None
        self.hum = None
        self.co2 = None
        
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
        db_manager.insert_measurement(self.device, 'bme280', self.lat, self.long, 'humidity', self.humidity_val)
        db_manager.insert_measurement(self.device, 'bme280', self.lat, self.long, 'pressure', self.pressure_val)
        db_manager.insert_measurement(self.device, 'bme280', self.lat, self.long, 'temperature', self.temperature_val)
        # Check if self has an attribute named 'wind_direction'
        if hasattr(self, 'wind_direction'):
            db_manager.insert_measurement(self.device, self.device_readings["device_name"], self.lat, self.long, 'wind_direction', self.wind_direction)
        # Check if self has an attribute named 'wind_speed'
        if hasattr(self, 'wind_speed'):
            db_manager.insert_measurement(self.device, self.device_readings["device_name"], self.lat, self.long, 'wind_speed', self.wind_speed)
        # Check if self has an attribute named 'rain_rate'
        if hasattr(self, 'rain_rate'):
            db_manager.insert_measurement(self.device, self.device_readings["device_name"], self.lat, self.long, 'rain_rate', self.rain_rate)
            
        
        config=sensor_values.set_time_interval_values(datetime.now().isoformat(), 
                                                              {'co2':self.co2_val,
                                                              'humidity':self.humidity_val,
                                                              'pressure': self.pressure_val,
                                                              'temperature': self.temperature_val})
        
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
        if interval == "min":
            # CO2
            insert_record_from_array(self, table, 'scd30', 'co2', config)
    
            # Pressure
            insert_record_from_array(self, table, 'bme280', 'pressure', config)
            
            # Humidity
            insert_record_from_array(self, table, 'bme280', 'humidity', config)
            
            # Temperature
            insert_record_from_array(self, table, 'bme280', 'temperature', config)
        else:            # CO2
            insert_record_from_value(self, table, 'scd30', 'co2', config)
    
            # Pressure
            insert_record_from_value(self, table, 'bme280', 'pressure', config)
            
            # Humidity
            insert_record_from_value(self, table, 'bme280', 'humidity', config)
            
            # Temperature
            insert_record_from_value(self, table, 'bme280', 'temperature', config)
        
    def read_values(self):
        co2_val=400
        while True:
            if self.scd.data_available:
                self.temp=self.scd.temperature
                self.hum=self.scd.relative_humidity
                self.co2=self.scd.CO2
    
                co2_val = self.co2
                if self.co2 < 5000:
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
        self.device_readings={}
        for device in deviceList:
            logger.info (f"-- {device.getDeviceName()}")
            self.device_readings["device_name"]=device.getDeviceName()
            genericPropertyList = device.getProperties()
        
            for genericProperty in genericPropertyList:
                logger.info (f"   > {genericProperty.getName()} {genericProperty.getTypeAsString()}")
        
                #if genericProperty.getType() == PyIndi.INDI_TEXT:
                #    for widget in PyIndi.PropertyText(genericProperty):
                #        print(
                #            f"       {widget.getName()}({widget.getLabel()}) = {widget.getText()}"
                #        )
        
                if genericProperty.getType() == PyIndi.INDI_NUMBER:
                    for widget in PyIndi.PropertyNumber(genericProperty):
                        #print(f"{widget.getName()}")
                        if "weather" in widget.getName().lower():
                            logger.info (
                                f"       {widget.getName()}({widget.getLabel()}) = {widget.getValue()}"
                            )
                            self.device_readings[widget.getName()]=widget.getValue()
                            if "rain_rate" in widget.getName().lower():
                                self.rain_rate = widget.getValue()
                            if "wind_speed" in widget.getName().lower():
                                self.wind_speed = widget.getValue()
                            if "wind_direction" in widget.getName().lower():
                                self.wind_direction = widget.getValue()
        
                if genericProperty.getType() == PyIndi.INDI_SWITCH:
                    for widget in PyIndi.PropertySwitch(genericProperty):
                        if "connect" in widget.getName().lower():
                            logger.info (
                                f"       {widget.getName()}({widget.getLabel()}) = {widget.getStateAsString()}"
                            )
        
                #if genericProperty.getType() == PyIndi.INDI_LIGHT:
                #    for widget in PyIndi.PropertyLight(genericProperty):
                #        print(
                #            f"       {widget.getLabel()}({widget.getLabel()}) = {widget.getStateAsString()}"
                #        )
        
                #if genericProperty.getType() == PyIndi.INDI_BLOB:
                #    for widget in PyIndi.PropertyBlob(genericProperty):
                #        print(
                #            f"       {widget.getName()}({widget.getLabel()}) = <blob {widget.getSize()} bytes>"
                #        )
        
        # Disconnect from the indiserver
        print("Disconnecting")
        indiClient.disconnectServer()
        print(self.device_readings)
          
        return co2_val
        
if __name__ == "__main__":
    array = ()
    sensor_reading = SensorModule()
    array = sensor_reading.get_sensor_readings()
