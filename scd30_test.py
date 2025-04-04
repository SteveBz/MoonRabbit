# SPDX-FileCopyrightText: 2020 by Bryan Siepert, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
import time
import board
import busio
import adafruit_scd30
import bme280 # pip3 install RPi.bme280
import smbus2

# BME280 sensor address (default address)
address = 0x76

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Load calibration parameters
calibration_params = bme280.load_calibration_params(bus, address)

sample_reading = bme280.sample(self.bus, SensorModule.ADDRESS, self.calibration_params)
self.temperature_val = sample_reading.temperature
self.humidity_val = sample_reading.humidity
self.pressure_val = sample_reading.pressure

# SCD-30 has tempremental I2C with clock stretching, datasheet recommends
# starting at 50KHz
i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
self.scd = adafruit_scd30.SCD30(i2c, ambient_pressure = int(self.pressure_val))
scd = adafruit_scd30.SCD30(i2c)
# scd.temperature_offset = 10
print("Temperature offset:", scd.temperature_offset)

# scd.measurement_interval = 4
print("Measurement interval:", scd.measurement_interval)

# scd.self_calibration_enabled = True
print("Self-calibration enabled:", scd.self_calibration_enabled)

# scd.ambient_pressure = 1100
print("Ambient Pressure:", scd.ambient_pressure)

# scd.altitude = 100
print("Altitude:", scd.altitude, "meters above sea level")

# scd.forced_recalibration_reference = 409
print("Forced recalibration reference:", scd.forced_recalibration_reference)
print("")

while True:
    
    sample_reading = bme280.sample(self.bus, SensorModule.ADDRESS, self.calibration_params)
    self.temperature_val = sample_reading.temperature
    self.humidity_val = sample_reading.humidity
    self.pressure_val = sample_reading.pressure
    self.scd = adafruit_scd30.SCD30(i2c_bus=self.i2c, ambient_pressure = int(self.pressure_val))
    data = scd.data_available
    if data:
        print("Data Available!")
        print("CO2:", scd.CO2, "PPM")
        print("Temperature:", scd.temperature, "degrees C")
        print("Humidity::", scd.relative_humidity, "%%rH")
        print("Pressure::", scd.ambient_pressure, "hPa")
        print("")
        print("Waiting for new data...")
        print("")

    time.sleep(0.5)
