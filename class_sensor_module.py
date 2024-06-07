import smbus2 # pip3 install smbus2
import bme280 # pip3 install RPi.bme280
import time 
import math
import busio # pip3 install adafruit-blinka
import board # pip3 install adafruit-blinka RPI.GPIO

#import adafruit_scd4x #pip3 install adafruit-circuitpython-scd4x
import adafruit_scd30 # pip3 install adafruit-circuitpython-scd30
from urllib.request import urlopen
from class_config_mgt import ConfigManager
from datetime import datetime, timedelta

from class_geoip_location_provider import LocationProvider

from class_database_mgt import DatabaseManager

import json
class SensorModule:
    PORT = 1
    ADDRESS = 0x76
    ADDRESS2 = 0x77
       
    def __init__(self):
        #print ("__init__")
        self.bus = smbus2.SMBus(SensorModule.PORT)
        try:
          self.calibration_params = bme280.load_calibration_params(self.bus, SensorModule.ADDRESS)
        except:
          self.calibration_params = bme280.load_calibration_params(self.bus, SensorModule.ADDRESS2)
          #print ("Using ADDRESS2")
          SensorModule.ADDRESS=SensorModule.ADDRESS2
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
        db_manager = DatabaseManager('measurement.db')
        # Commit the changes and close the connection
        db_manager.conn.commit()
        db_manager.conn.close()
        config_manager = ConfigManager()
        self.lat=config_manager.get_lat()
        self.long=config_manager.get_long()
        self.device=config_manager.get_device_id()
        # SCD-30 has tempremental I2C with clock stretching, datasheet recommends
        # starting at 50KHz
        self.i2c = busio.I2C(board.SCL, board.SDA) # uses board.SCL and board.SDA
        sample_reading = bme280.sample(self.bus, SensorModule.ADDRESS, self.calibration_params)
        self.temperature_val = sample_reading.temperature
        self.humidity_val = sample_reading.humidity
        self.pressure_val = sample_reading.pressure
        self.scd = adafruit_scd30.SCD30(i2c_bus=self.i2c, ambient_pressure = int(self.pressure_val))
        self.scd.self_calibration_enabled=False
        #self.co2_val = self.read_co2()
        #print ("exiting __init__")

    def __del__(self):
        if self.bus is not None:
            self.bus.close()
        
    def get_sensor_readings(self):
        #print ("get_sensor_readings")
        self.co2_val = self.read_co2()
        # Allow for zero value temp or hum in BME280
        if self.humidity_val==0 and self.hum != 0:
            self.humidity_val=self.hum
        if self.temperature_val==0 and self.hum != 0:
            self.temperature_val=self.temp
        #print(1)
        config_manager = ConfigManager()
        db_manager = DatabaseManager('measurement.db')
        db_manager.insert_measurement(self.device, 'scd30', self.lat, self.long, 'co2', self.co2_val)
        db_manager.insert_measurement(self.device, 'bme280', self.lat, self.long, 'humidity', self.humidity_val)
        db_manager.insert_measurement(self.device, 'bme280', self.lat, self.long, 'pressure', self.pressure_val)
        db_manager.insert_measurement(self.device, 'bme280', self.lat, self.long, 'temperature', self.temperature_val)
        config=config_manager.set_time_interval_values(datetime.now().isoformat(), 
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
            config=config_manager.remove_interval(interval)
        
        start_time = datetime.fromisoformat(config["time_intervals"]["hour"]["start"])
        end_mins = (start_time + timedelta(hours=1)).replace(microsecond=0)      
        mean_time =(start_time + timedelta(minutes=30)).replace(microsecond=0)      
        if datetime.now()> end_mins:
            interval="hour"
            self.aggregate_interval("sensor_measurement_hours", interval, mean_time, config, db_manager)
            config=config_manager.remove_interval(interval)
            
        start_time = datetime.fromisoformat(config["time_intervals"]["day"]["start"])
        end_mins = (start_time + timedelta(days=1)).replace(microsecond=0)      
        mean_time =(start_time + timedelta(hours=12)).replace(microsecond=0)      
        if datetime.now()> end_mins:
            interval="day"
            self.aggregate_interval("sensor_measurement_days", interval, mean_time, config, db_manager)
            config=config_manager.remove_interval(interval)

        # Commit the changes and close the connection
        db_manager.conn.commit()
        db_manager.conn.close()
        
        retval=(self.temperature_val, self.pressure_val, self.humidity_val, self.co2_val, self.lat, self.long)
            
        print(datetime.now(), f"Latitude: {self.lat}, ", f"Longitude: {self.long}", f"Temperature: {self.temperature_val:.1f} *C, ", f"Humidity: {self.humidity_val:,.1f} %", f"CO2: {int(self.co2_val):,d} ppm", f"Pressure: {int(self.pressure_val):,d} mBars")
        
        return retval

    def aggregate_interval(self, table, interval, mean_time, config, db_manager):
        print (f"{interval} aggregate")
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
        
    def read_co2(self):
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
        return co2_val
        
if __name__ == "__main__":
    array = ()
    sensor_reading = SensorModule()
    array = sensor_reading.get_sensor_readings()
