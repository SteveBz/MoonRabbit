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

sample_reading = bme280.sample(bus, address, calibration_params)
temperature_val = sample_reading.temperature
humidity_val = sample_reading.humidity
pressure_val = sample_reading.pressure
ambient_pressure_hpa = int(pressure_val)

# SCD-30 has tempremental I2C with clock stretching, datasheet recommends
# starting at 50KHz
i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
#scd = adafruit_scd30.SCD30(i2c, ambient_pressure = int(ambient_pressure_hpa))
scd = adafruit_scd30.SCD30(i2c)
print("Warming up the SCD30 sensor...")
time.sleep(5)

# scd.temperature_offset = 10
print("Temperature offset:", scd.temperature_offset)

scd.measurement_interval = 4
print("Measurement interval:", scd.measurement_interval)

# scd.self_calibration_enabled = True
print("Self-calibration enabled:", scd.self_calibration_enabled)

scd.ambient_pressure = int(ambient_pressure_hpa)
print("Ambient Pressure:", scd.ambient_pressure)

# scd.altitude = 100
print("Altitude:", scd.altitude, "meters above sea level")

#scd.forced_recalibration_reference = 409
print("Forced recalibration reference:", scd.forced_recalibration_reference)
print("")

while True:
    
    sample_reading = bme280.sample(bus, address, calibration_params)
    temperature_val = sample_reading.temperature
    humidity_val = sample_reading.humidity
    pressure_val = sample_reading.pressure
    ambient_pressure_hpa = int(sample_reading.pressure)
    
    # Update ambient pressure *without* reinitializing the sensor
    scd.ambient_pressure = ambient_pressure_hpa
    scd.temperature_offset = scd.temperature - temperature_val
    
    time.sleep(2)
    data = scd.data_available
    if data:
        print("Data Available!")
        print(f"CO2: {scd.CO2:.1f} ppm")
        print(f"Temperature: {scd.temperature:.1f} °C")
        print(f"Temperature offset: {(scd.temperature - temperature_val):.1f} °C")
        print(f"Humidity: {scd.relative_humidity:.1f} %RH")
        print(f"Ambient Pressure (BME280): {ambient_pressure_hpa} hPa")
        print("")
        print("Waiting for new data...")
        print("")

    time.sleep(2)
