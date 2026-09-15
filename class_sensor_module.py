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
import threading
import paho.mqtt.client as mqtt
import subprocess

# Set up logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
import os
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
        logger.info(f"PATH = {os.environ.get('PATH')}")
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

        # MQTT client for receiving Vantage weather data from indi2mqtt
        self.device_readings = {}
        self._mqtt_lock = threading.Lock()
        self._first_mqtt_message = threading.Event()
        self._stop_watchdog = threading.Event()
        self._last_vantage_update = 0.0
        self._ensure_vantage_connected()          # one attempt at startup
        threading.Thread(target=self._vantage_watchdog, daemon=True).start()
        self._mqtt_client = mqtt.Client()
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_message = self._on_mqtt_message
        self.use_vantage = False
        try:
            self._mqtt_client.connect("localhost", 1883, 60)
            self._mqtt_client.loop_start()
            
            got = self._first_mqtt_message.wait(timeout=30)
            with self._mqtt_lock:
                self.use_vantage = got and bool(self.device_readings)
            logger.info(f"Vantage present at startup: {self.use_vantage} (got_message={got})")
            logger.info("MQTT client connected to localhost:1883")
        except Exception as e:
            logger.error(f"MQTT connect failed: {e}")
        
        lock = FileLock("SensorModule", lock_dir='locks')  # Use a dedicated directory for lock files
        lock.release_lock(force=True)

    def __del__(self):
        if getattr(self, "_stop_watchdog", None):
            self._stop_watchdog.set()
        if getattr(self, "_mqtt_client", None):
            try:
                self._mqtt_client.loop_stop()
                self._mqtt_client.disconnect()
            except Exception:
                pass
        if self.bus is not None:
            self.bus.close()
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        logger.info(f"MQTT connected (rc={rc}), subscribing to indiserver/vantage/#")
        client.subscribe("indiserver/vantage/#")

    def _on_mqtt_message(self, client, userdata, msg):
        tail = msg.topic.rsplit("/", 1)[-1].lower()
        try:
            value = float(msg.payload.decode())
        except (ValueError, UnicodeDecodeError):
            return
        with self._mqtt_lock:
            if   "temperature"    in tail: self.device_readings["temperature"]    = value
            elif "humidity"       in tail: self.device_readings["humidity"]       = value
            elif "barometer"      in tail or "pressure" in tail:
                self.device_readings["pressure"] = value
            elif "wind_speed"     in tail: self.device_readings["wind_speed"]     = value
            elif "wind_direction" in tail: self.device_readings["wind_direction"] = value
            elif "rain_rate"      in tail: self.device_readings["rain_rate"]      = value
            self.device_readings["device_name"] = "vantage_pro"
        self._first_mqtt_message.set()
        self._last_vantage_update = time.time()

    def _vantage_property_present(self):
        """True iff the Vantage driver is loaded and its CONNECTION property exists."""
        try:
            r = subprocess.run(
                ["indi_getprop", "-h", "localhost", "Vantage.CONNECTION.*"],
                capture_output=True, text=True, timeout=5
            )
            return "CONNECT=" in r.stdout
        except Exception:
            return False
    
    def _ensure_vantage_connected(self):
        """If driver is loaded and device disconnected, send CONNECT. Idempotent."""
        if not self._vantage_property_present():
            return                                    # nothing to act on
        try:
            r = subprocess.run(
                ["indi_getprop", "-h", "localhost", "Vantage.CONNECTION.CONNECT"],
                capture_output=True, text=True, timeout=5
            )
            if "=On" in r.stdout:
                return                                # already connected
        except Exception:
            return
        try:
            subprocess.run(
                ["indi_setprop",
                 "Vantage.CONNECTION.CONNECT=On",
                 "Vantage.CONNECTION.DISCONNECT=Off"],
                timeout=5, capture_output=True
            )
            logger.info("Sent CONNECT to Vantage")
        except Exception as e:
            logger.warning(f"Vantage CONNECT failed: {e}")
    
    def _vantage_watchdog(self):
        while not self._stop_watchdog.is_set():
            self._ensure_vantage_connected()
            self._stop_watchdog.wait(60)
            
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
        # If Vantage was present at startup, override BME280 values with latest MQTT readings
        vantage_fresh = (time.time() - self._last_vantage_update) < 60
        if vantage_fresh and self.device_readings:
            with self._mqtt_lock:
                if "temperature" in self.device_readings:
                    self.temperature_val = self.device_readings["temperature"]
                if "humidity" in self.device_readings:
                    self.humidity_val = self.device_readings["humidity"]
                if "pressure" in self.device_readings:
                    self.pressure_val = self.device_readings["pressure"]
                # Wind and rain for aggregate tracking
                self.wind_speed     = self.device_readings.get("wind_speed")
                self.wind_direction = self.device_readings.get("wind_direction")
                self.rain_rate      = self.device_readings.get("rain_rate")
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

        # CO2 always comes from the SCD30
        db_manager.insert_measurement(self.device, 'scd30', self.lat, self.long, 'co2', self.co2_val)


        vantage_fresh = (time.time() - self._last_vantage_update) < 60
        if vantage_fresh and self.device_readings:
            # One insert per reading type, values from MQTT cache
            source_sensor = self.device_readings.get("device_name", "vantage_pro")
            logger.info(f"DEBUG: use_vantage=True, source_sensor={source_sensor}")
            logger.info(f"DEBUG: device_readings keys = {list(self.device_readings.keys())}")
            for key in ('temperature', 'humidity', 'pressure',
                        'wind_speed', 'wind_direction', 'rain_rate'):
                if key in self.device_readings:
                    value = self.device_readings[key]
                    logger.info(f"DEBUG: inserting {key} = {value} (sensor={source_sensor})")
                    db_manager.insert_measurement(
                        self.device, source_sensor, self.lat, self.long,
                        key, value)
                else:
                    logger.info(f"DEBUG: {key} not in device_readings, skipping")
        else:
            # No Vantage: temp/hum/pressure come from the BME280 values
            source_sensor = 'bme280'
            logger.info(f"DEBUG: use_vantage=False, inserting bme280 temp/hum/pressure")
            db_manager.insert_measurement(self.device, source_sensor, self.lat, self.long, 'temperature', self.temperature_val)
            db_manager.insert_measurement(self.device, source_sensor, self.lat, self.long, 'humidity',    self.humidity_val)
            db_manager.insert_measurement(self.device, source_sensor, self.lat, self.long, 'pressure',    self.pressure_val)

        
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
            if not sensor_reading_array:
                logger.info(f"DEBUG: skipping empty array for {reading_type}")
                return
            db_manager.insert_aggregate_data(table, mean_time, self.device, sensor_type, self.lat, self.long, reading_type, 
                sum(sensor_reading_array)/len(sensor_reading_array), 
                max(sensor_reading_array), 
                min(sensor_reading_array))
                
        def insert_record_from_value(self, table, sensor_type, reading_type, config):
            sensor_readings = config["time_intervals"][interval]
            #print(sensor_readings)
            if not sensor_readings.get("count"):
                logger.info(f"DEBUG: skipping zero-count interval for {reading_type}")
                return
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
        #self.device_readings={}
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
        
        return co2_val
        
if __name__ == "__main__":
    array = ()
    sensor_reading = SensorModule()
    array = sensor_reading.get_sensor_readings()
