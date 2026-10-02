import smbus2 # pip3 install smbus2
import math
import busio # pip3 install adafruit-blinka
import board # pip3 install adafruit-blinka RPI.GPIO


import bme280 # pip3 install RPi.bme280
#import adafruit_scd4x #pip3 install adafruit-circuitpython-scd4x
import adafruit_scd30 # pip3 install adafruit-circuitpython-scd30

import logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- New sensors (SHT41 temp/humidity, SGP41 VOC/NOx) ---
# pip install adafruit-circuitpython-sht4x adafruit-circuitpython-sgp41
try:
    from adafruit_sht4x import SHT4x
    SHT4X_AVAILABLE = True
except ImportError:
    SHT4X_AVAILABLE = False

try:
    from adafruit_sgp41.sgp41 import SGP41
    SGP41_AVAILABLE = True
except Exception as e:
    import traceback
    logger.error(f"SGP41 import failed: {type(e).__name__}: {e}")
    traceback.print_exc()
    SGP41_AVAILABLE = False

from adafruit_sgp41.gas_index_algorithm import (
    GasIndexAlgorithm,
    ALGORITHM_TYPE_VOC,
    ALGORITHM_TYPE_NOX,
)

try:
    from adafruit_tsl2591 import TSL2591
    TSL2591_AVAILABLE = True
except ImportError:
    TSL2591_AVAILABLE = False

from urllib.request import urlopen
from class_config_mgt import ConfigManager
from datetime import datetime, timedelta
import time 

from class_geoip_location_provider import LocationProvider
from class_database_mgt import DatabaseManager
# for logging
import sys
import time
import threading
import paho.mqtt.client as mqtt
import subprocess

import os
import json
#from class_shipLog import logShipping
from class_file_lock import FileLock
class SensorModule:
    PORT = 1
    ADDRESS = 0x76
    ADDRESS2 = 0x77
    CUMULATIVE_KEYS = {'rain_mm'}
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
        self._mqtt_reconnect_attempts = 0

        self.SENSOR_SOURCE_MAP = {
            'co2': 'scd30',
            'humidity': 'bme280',
            'pressure': 'bme280',
            'temperature': 'bme280',
            'wind_speed': 'vantage_pro',
            'wind_direction': 'vantage_pro',
            'rain_rate': 'vantage_pro',
            'rain_mm':   'vantage_pro',
            'rain_today':'vantage_pro',
            'rain_hourly': 'ecowitt',
            'uv_index':'ecowitt',
        }

        self.ECOWITT_MAP = {
            'tempf':         'temperature',
            'tempc':         'temperature',
            'humidity':      'humidity',
            'baromrelin':    'pressure',
            'baromabsin':    'pressure',
            'windspeedmph':  'wind_speed',
            'winddir':       'wind_direction',
            'rainratein':    'rain_rate',
            'hourlyrainin':  'rain_hourly',
            'dailyrainin':   'rain_today',
            'solarradiation':'solar_radiation',
            'uv':            'uv_index',
        }
        
        self.ATTR_TO_READING = {
            'co2_val': 'co2',
            'humidity_val': 'humidity',
            'pressure_val': 'pressure',
            'temperature_val': 'temperature',
            'wind_speed': 'wind_speed',
            'wind_direction': 'wind_direction',
            'rain_rate': 'rain_rate',
            'rain_mm': 'rain_mm',
        }
        
        self._last_rain_time = None
        self.rain_today = 0.0        # mm since midnight
        self._rain_day = None        # date of current total
        
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
        self.sht41 = None
        self.sgp41 = None
        self.have_sht41 = False
        self.have_sgp41 = False

        self.voc_index   = None
        self.nox_index   = None
        self.voc_raw     = None
        self.nox_raw     = None
        self._voc_alg    = None
        self._nox_alg    = None
        self._sgp41_lock = threading.Lock()
        self._stop_sgp41 = threading.Event()
        
        self.tsl2591 = None
        self.have_tsl2591 = False
        self.lux_val = None
        self.visible_val = None
        self.infrared_val = None
        self.full_spectrum_val = None

        config_manager = ConfigManager("config.json")
        self.lat=config_manager.get_lat()
        self.long=config_manager.get_long()
        self.device=config_manager.get_device_id()
        self.is_registered=config_manager.is_registered()
        self.weather_source = config_manager.get_weather_source()
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

        # --- SHT41 (temperature + humidity) ---
        if SHT4X_AVAILABLE:
            try:
                self.sht41 = SHT4x(self.i2c)
                self.have_sht41 = True
                logger.info("SHT41: opened OK")
            except Exception as e:
                logger.error(f"SHT41: failed to open -> {e}")
        else:
            logger.warning("SHT41: library not installed")
        
        # --- SGP41 (VOC / NOx) ---# --- SGP41 (VOC / NOx) ---
        if SGP41_AVAILABLE:
            try:
                self.sgp41 = SGP41(self.i2c)
                logger.info("SGP41: opened OK")
        
                # 10 s conditioning — best if sensor has been off >10 h
                logger.info("SGP41: running conditioning (10 s)...")
                self.sgp41.conditioning()
                logger.info("SGP41: conditioning complete")
        
                # Gas Index Algorithm instances (1 Hz sampling internally)
                self._voc_alg = GasIndexAlgorithm(ALGORITHM_TYPE_VOC)
                self._nox_alg = GasIndexAlgorithm(ALGORITHM_TYPE_NOX)
        
                self.have_sgp41 = True
                threading.Thread(target=self._sgp41_sampler, daemon=True).start()
                logger.info("SGP41: 1 Hz sampler thread started")
            except Exception as e:
                logger.error(f"SGP41: init failed -> {e}")
                self.have_sgp41 = False
        else:
            logger.warning("SGP41: library not installed")
        
        # Register VOC/NOx in the source/attribute maps if SGP41 is present
        if self.have_sgp41:
            self.SENSOR_SOURCE_MAP['voc'] = 'sgp41'
            self.SENSOR_SOURCE_MAP['nox'] = 'sgp41'
            self.ATTR_TO_READING['voc_index'] = 'voc'
            self.ATTR_TO_READING['nox_index'] = 'nox'
        
        logger.info(f"have_sht41={self.have_sht41}  have_sgp41={self.have_sgp41}")

        # Re-attribute T/H to SHT41 for aggregates if it's present
        if self.have_sht41:
            self.SENSOR_SOURCE_MAP['temperature'] = 'sht41'
            self.SENSOR_SOURCE_MAP['humidity']    = 'sht41'
        
        # --- TSL2591 (luminosity) ---
        if TSL2591_AVAILABLE:
            try:
                self.tsl2591 = TSL2591(self.i2c)
                # Defaults are GAIN_MED (25x) and INTEGRATIONTIME_100MS.
                # For outdoor/bright conditions, reduce gain to GAIN_LOW.
                # For very dim conditions, increase to GAIN_HIGH or GAIN_MAX.
                self.have_tsl2591 = True
                logger.info("TSL2591: opened OK")
            except Exception as e:
                logger.error(f"TSL2591: failed to open -> {e}")
        else:
            logger.warning("TSL2591: library not installed")
        
        if self.have_tsl2591:
            self.SENSOR_SOURCE_MAP['lux']          = 'tsl2591'
            self.SENSOR_SOURCE_MAP['visible']      = 'tsl2591'
            self.SENSOR_SOURCE_MAP['infrared']     = 'tsl2591'
            self.SENSOR_SOURCE_MAP['full_spectrum'] = 'tsl2591'
            self.ATTR_TO_READING['lux_val']           = 'lux'
            self.ATTR_TO_READING['visible_val']       = 'visible'
            self.ATTR_TO_READING['infrared_val']      = 'infrared'
            self.ATTR_TO_READING['full_spectrum_val'] = 'full_spectrum'

        # MQTT client for receiving Vantage weather data from indi2mqtt
        self.device_readings = {}
        self._mqtt_lock = threading.Lock()
        self._first_mqtt_message = threading.Event()
        self._stop_watchdog = threading.Event()
        self._last_vantage_update = 0.0
        if self.weather_source == 'vantage':
            self._ensure_vantage_connected()          # one attempt at startup
            threading.Thread(target=self._vantage_watchdog, daemon=True).start()
        self._mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_message = self._on_mqtt_message
        self.use_vantage = False
        try:
            self._mqtt_client.connect("localhost", 1883, 60)
            self._mqtt_client.loop_start()
            
            logger.info("MQTT client connected to localhost:1883")
        except Exception as e:
            logger.error(f"MQTT connect failed: {e}")
        
        lock = FileLock("SensorModule", lock_dir='locks')  # Use a dedicated directory for lock files
        lock.release_lock(force=True)

    def __del__(self):
        if getattr(self, "_stop_sgp41", None):
            self._stop_sgp41.set()
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
        logger.info(f"MQTT connected (rc={rc})")
        if self.weather_source == 'vantage':
            client.subscribe("indiserver/vantage/#")
        elif self.weather_source == 'ecowitt':
            client.subscribe("ecowitt/#")
        # 'none': no weather subscription

    def _ecowitt_to_metric(self, key, value):
        """Convert ecowitt2mqtt's imperial defaults to metric.
        If ecowitt2mqtt is run with --output-unit-system=metric, these are no-ops."""
        if key == 'temperature':
            return (value - 32.0) * 5.0 / 9.0
        if key == 'wind_speed':
            return value * 0.44704
        if key in ('rain_rate', 'rain_hourly', 'rain_today'):
            return value * 25.4
        if key == 'pressure':
            return value * 33.8639
        return value
    
    def _on_mqtt_message(self, client, userdata, msg):
        tail = msg.topic.rsplit("/", 1)[-1].lower()
        try:
            value = float(msg.payload.decode())
        except (ValueError, UnicodeDecodeError):
            return
        with self._mqtt_lock:
            if self.weather_source == 'ecowitt':
                key = self.ECOWITT_MAP.get(tail)
                if key is None:
                    return
                value = self._ecowitt_to_metric(key, value)
                self.device_readings[key] = value
                self.device_readings["device_name"] = "ecowitt"
            else:
                # Vantage path (unchanged)
                if   "temperature"    in tail: self.device_readings["temperature"]    = value
                elif "humidity"       in tail: self.device_readings["humidity"]       = value
                elif "barometer"      in tail or "pressure" in tail:
                    self.device_readings["pressure"] = value
                elif "wind_speed"     in tail: self.device_readings["wind_speed"]     = value
                elif "wind_direction" in tail: self.device_readings["wind_direction"] = value
                elif "rain_rate"      in tail:
                    self.device_readings["rain_rate"] = value
                    now = time.time()
                    if self._last_rain_time is not None:
                        dt_h = (now - self._last_rain_time) / 3600.0
                        if dt_h < 0.1:
                            inc = value * dt_h
                            self.device_readings["rain_mm"] = (
                                self.device_readings.get("rain_mm", 0.0) + inc
                            )
                            self.rain_today += inc
                    self._last_rain_time = now
                self.device_readings["device_name"] = "vantage_pro"
        self._first_mqtt_message.set()
        self._last_vantage_update = time.time()

    def _vantage_property_present(self):
        """True iff the Vantage driver is loaded and its CONNECTION property exists."""
        try:
            r = subprocess.run(
                ["/usr/bin/indi_getprop", "-h", "localhost", "Vantage.CONNECTION.*"],
                capture_output=True, text=True, timeout=5
            )
            return "CONNECT=" in r.stdout
        except FileNotFoundError:
            logger.warning("indi_getprop not found — check PATH or use absolute path")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("indi_getprop timed out")
            return False
        except Exception as e:
            logger.warning(f"Vantage property check failed: {e}")
            return False
    
    def _ensure_vantage_connected(self):
        """If driver is loaded and device disconnected, send CONNECT. Idempotent."""
        if not self._vantage_property_present():
            return                                    # nothing to act on
        try:
            r = subprocess.run(
                ["/usr/bin/indi_getprop", "-h", "localhost", "Vantage.CONNECTION.CONNECT"],
                capture_output=True, text=True, timeout=5
            )
            if "=On" in r.stdout:
                return                                # already connected
        except FileNotFoundError:
            logger.warning("indi_getprop not found — check PATH or use absolute path")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("indi_getprop timed out")
            return False
        except Exception as e:
            logger.warning(f"Vantage property check failed: {e}")
            return False
    
        try:
            subprocess.run(
                ["/usr/bin/indi_setprop",
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

            # MQTT staleness check
            if self._last_vantage_update > 0:
                silence = time.time() - self._last_vantage_update
                
                if silence > 300:                            # 5 minutes → restart indi2mqtt 
                    target = 'indi2mqtt' if self.weather_source == 'vantage' else 'ecowitt2mqtt'
                    logger.warning(f"MQTT silent for {silence:.0f}s — restarting {target} via supervisor")
                    try:
                        subprocess.run(
                            ["sudo", "supervisorctl", "restart", target],
                            timeout=15, capture_output=True
                        )
                    except Exception as e:
                        logger.error(f"supervisorctl restart failed: {e}")
                    time.sleep(10)                            # let indi2mqtt settle
                    self._last_vantage_update = time.time()  # avoid immediate re-trigger
                elif silence > 180:                     # 3 minutes with no messages
                    logger.warning(f"MQTT silent for {silence:.0f}s — reconnecting client")
                    try:
                        self._mqtt_client.loop_stop()
                        self._mqtt_client.disconnect()
                    except Exception:
                        pass
                    try:
                        self._mqtt_client.connect("localhost", 1883, 60)
                        self._mqtt_client.loop_start()
                        logger.info("MQTT client reconnected")
                    except Exception as e:
                        logger.error(f"MQTT reconnect failed: {e}")
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
    def _read_bme280(self):
        try:
            sample = bme280.sample(self.bus, SensorModule.ADDRESS, self.calibration_params)
            self.temperature_val = sample.temperature
            self.humidity_val    = sample.humidity
            self.pressure_val    = sample.pressure
        except Exception as e:
            logger.error(f"BME280 read failed: {e}")

    def _read_sht41(self):
        """If SHT41 present, override BME280 temperature/humidity with its readings."""
        if not self.have_sht41:
            return
        try:
            self.temperature_val = self.sht41.temperature
            self.humidity_val    = self.sht41.relative_humidity
        except Exception as e:
            logger.error(f"SHT41 read failed: {e}")

    def _sgp41_sampler(self):
        """Sample SGP41 at 1 Hz, run gas index algorithms, cache latest indices."""
        next_tick = time.monotonic()
        while not self._stop_sgp41.is_set():
            try:
                t = self.temperature_val if self.temperature_val is not None else 25.0
                h = self.humidity_val    if self.humidity_val    is not None else 50.0
                t = max(-10.0, min(50.0,  t))
                h = max(  0.0, min(100.0, h))
    
                self.sgp41.temperature = t
                self.sgp41.relative_humidity = h
    
                voc_raw, nox_raw = self.sgp41.measure_raw()
                voc_idx = self._voc_alg.process(voc_raw)
                nox_idx = self._nox_alg.process(nox_raw)
    
                with self._sgp41_lock:
                    self.voc_raw   = voc_raw
                    self.nox_raw   = nox_raw
                    self.voc_index = voc_idx
                    self.nox_index = nox_idx
            except Exception as e:
                logger.error(f"SGP41 sample failed: {e}")
    
            # Maintain a strict 1 Hz cadence regardless of how long the I2C call took
            next_tick += 1.0
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                self._stop_sgp41.wait(sleep_for)
            else:
                next_tick = time.monotonic()  # we fell behind; resync
                    
    def _read_tsl2591(self):
        """Read lux, visible, infrared, and full spectrum from the TSL2591."""
        if not self.have_tsl2591:
            return
        try:
            self.lux_val           = self.tsl2591.lux
            self.visible_val       = self.tsl2591.visible
            self.infrared_val      = self.tsl2591.infrared
            self.full_spectrum_val = self.tsl2591.full_spectrum
        except Exception as e:
            logger.error(f"TSL2591 read failed: {e}")
            
    def get_sensor_readings(self):
        print ("get_sensor_readings")
        # Re-read BME280 first – Vantage may not be available
        self._read_bme280()
        # SHT41 (if present) overrides BME280 T/H before SCD30 offset calc
        self._read_sht41()
        self._read_tsl2591()
        
        with self._sgp41_lock:
            voc_idx = self.voc_index
            nox_idx = self.nox_index
        
        self.co2_val = self.read_values()
        today = datetime.now().date()
        if self._rain_day != today:
            self.rain_today = 0.0
            self._rain_day = today
        self.device_readings["rain_today"] = self.rain_today
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
                self.rain_mm        = self.device_readings.get("rain_mm", 0.0)
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
        if voc_idx is not None:
            db_manager.insert_measurement(self.device, 'sgp41', self.lat, self.long, 'voc', voc_idx)
        if nox_idx is not None:
            db_manager.insert_measurement(self.device, 'sgp41', self.lat, self.long, 'nox', nox_idx)
        
        if self.lux_val is not None:
            db_manager.insert_measurement(self.device, 'tsl2591', self.lat, self.long, 'lux', self.lux_val)
        
        vantage_fresh = (time.time() - self._last_vantage_update) < 60
        if vantage_fresh and self.device_readings:
            # One insert per reading type, values from MQTT cache
            source_sensor = self.device_readings.get("device_name", "vantage_pro")
            logger.info(f"DEBUG: vantage_fresh=True, source_sensor={source_sensor}")
            logger.info(f"DEBUG: device_readings keys = {list(self.device_readings.keys())}")
            for key in ('temperature', 'humidity', 'pressure',
                        'wind_speed', 'wind_direction', 'rain_rate',
                        'rain_mm', 'rain_today'):
                if key in self.device_readings:
                    if key == 'rain_mm':
                        with self._mqtt_lock:
                            value = self.device_readings.get("rain_mm", 0.0)
                    else:
                        value = self.device_readings[key]
                    logger.info(f"DEBUG: inserting {key} = {value} (sensor={source_sensor})")
                    db_manager.insert_measurement(
                        self.device, source_sensor, self.lat, self.long,
                        key, value)
                else:
                    logger.info(f"DEBUG: {key} not in device_readings, skipping")
        else:
            # No Vantage: pressure is always BME280; temp/hum come from SHT41 if present
            th_sensor = 'sht41' if self.have_sht41 else 'bme280'
            logger.info(f"DEBUG: vantage_fresh=False, inserting temp/hum from {th_sensor}, pressure from bme280")
            db_manager.insert_measurement(self.device, th_sensor,  self.lat, self.long, 'temperature', self.temperature_val)
            db_manager.insert_measurement(self.device, th_sensor,  self.lat, self.long, 'humidity',    self.humidity_val)
            db_manager.insert_measurement(self.device, 'bme280',   self.lat, self.long, 'pressure',    self.pressure_val)    
        
        values = {}
        for attr, key in self.ATTR_TO_READING.items():
            val = getattr(self, attr, None)
            if val is not None:
                values[key] = val

        # Snapshot taken into `values`; now safe to reset the accumulator.
        # The MQTT thread may have added more since we read it — reset under lock.
        with self._mqtt_lock:
            self.device_readings["rain_mm"] = 0.0
            self.rain_mm = 0.0

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
        lux_str  = f"Lux: {self.lux_val:.0f}" if self.lux_val is not None else "Lux: n/a"
        voc_str  = f"VOC: {voc_idx}" if voc_idx is not None else "VOC: n/a"
        nox_str  = f"NOx: {nox_idx}" if nox_idx is not None else "NOx: n/a"
        scd_t_str = f"SCD30_T: {self.temp:.1f} *C" if self.temp is not None else "SCD30_T: n/a"
        
        log_message = (
            f"{datetime.now().isoformat()} - "
            f"Latitude: {self.lat}, "
            f"Longitude: {self.long}, "
            f"Temperature: {self.temperature_val:.1f} *C, "
            f"{scd_t_str}, "
            f"Humidity: {self.humidity_val:.1f} %, "
            f"CO2: {int(self.co2_val):,d} ppm, "
            f"Pressure: {int(self.pressure_val):,d} mBars, "
            f"{lux_str}, "
            f"{voc_str}, "
            f"{nox_str}"
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
            if reading_type == 'wind_direction':
                sin_sum = sum(math.sin(math.radians(d)) for d in sensor_reading_array)
                cos_sum = sum(math.cos(math.radians(d)) for d in sensor_reading_array)
                mean_val = math.degrees(math.atan2(sin_sum, cos_sum)) % 360
                # max/min are meaningless on a circular scale — record 0 for both
                max_val = 0
                min_val = 0
            else:
                mean_val = sum(sensor_reading_array) / len(sensor_reading_array)
                max_val = max(sensor_reading_array)
                min_val = min(sensor_reading_array)
            
            db_manager.insert_aggregate_data(table, mean_time, self.device, sensor_type, self.lat, self.long, reading_type,
                mean_val, max_val, min_val)
                
        def insert_record_from_value(self, table, sensor_type, reading_type, config):
            sensor_readings = config["time_intervals"][interval]
            #print(sensor_readings)
            if not sensor_readings.get("count"):
                logger.info(f"DEBUG: skipping zero-count interval for {reading_type}")
                return
            divisor = 1 if reading_type in self.CUMULATIVE_KEYS else sensor_readings["count"]
            db_manager.insert_aggregate_data(table, mean_time, self.device, sensor_type, self.lat, self.long, reading_type, 
                sensor_readings[reading_type]/ divisor, 
                0, # max - sort out later 
                0) # min - sort out later

        # NEW dynamic loop
        interval_data = config["time_intervals"][interval]
        
        if interval == "min":
            for reading_type, sensor_type in self.SENSOR_SOURCE_MAP.items():
                if reading_type not in interval_data:
                    continue
                if reading_type in self.CUMULATIVE_KEYS:
                    arr = interval_data[reading_type]
                    if arr:
                        db_manager.insert_aggregate_data(
                            table, mean_time, self.device,
                            sensor_type, self.lat, self.long, reading_type,
                            sum(arr), max(arr), min(arr))
                else:
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
                    raw_offset = self.temp - self.temperature_val
                    offset = max(0.0, min(655.35, raw_offset))
                
                    # Log whenever the situation is unusual — negative offset, or clamp active
                    if raw_offset < 0:
                        logger.warning(
                            f"SCD30 offset negative: scd30={self.temp:.2f} °C, "
                            f"reference={self.temperature_val:.2f} °C, "
                            f"raw_offset={raw_offset:.2f} °C — clamping to 0"
                        )
                    elif raw_offset > 10.0:
                        logger.warning(
                            f"SCD30 offset unusually large: scd30={self.temp:.2f} °C, "
                            f"reference={self.temperature_val:.2f} °C, "
                            f"raw_offset={raw_offset:.2f} °C"
                        )
                
                    self.temperature_offset = offset
                    try:
                        self.scd.temperature_offset = offset
                    except Exception as e:
                        logger.warning(
                            f"SCD30 temperature_offset rejected: {e} "
                            f"(scd30={self.temp:.2f} °C, "
                            f"reference={self.temperature_val:.2f} °C, "
                            f"clamped_offset={offset:.2f} °C)"
                        )
                    
                co2_val = self.co2
                if self.co2 < MAX_VALID_CO2:
                        break
            time.sleep(1)
        
        return co2_val
        
if __name__ == "__main__":
    array = ()
    sensor_reading = SensorModule()
    array = sensor_reading.get_sensor_readings()
