import argparse
import board
import busio
import adafruit_scd30
import bme280 # pip3 install RPi.bme280
import time

class SCD30:
    def __init__(self):
        # Initialize I2C bus and SCD30 sensor
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.scd30 = adafruit_scd30.SCD30(self.i2c)

    def set_ambient_pressure_from_bme280(self):
        if not self.pressure_source:
            raise RuntimeError("BME280 pressure source not initialized")
        pressure_hpa = self.pressure_source['pressure']
        self.scd30.ambient_pressure = int(pressure_hpa)
        print(f"Ambient pressure set to {int(pressure_hpa)} mbar from BME280")
    
    def set_forced_recalibration_reference(self, value):
        self.scd30.forced_recalibration_reference = value
        print(f"Forced recalibration reference set to {value} ppm")

def main():
    parser = argparse.ArgumentParser(description='SCD30 sensor test.')
    parser.add_argument('-f', '--forced-recal', type=int, help='The forced recalibration reference value in ppm')
    args = parser.parse_args()

    try:
#        scd30 = SCD30()
        # Set up BME280 using smbus2
        port = 1
        address = 0x76  # Adjust if your BME280 is at 0x77
        bus = smbus2.SMBus(port)
        bme280_calibration = bme280.load_calibration_params(bus, address)
        bme280_data = bme280.sample(bus, address, bme280_calibration)

        # Pass BME280 pressure data to SCD30
        scd30 = SCD30(pressure_source=bme280_data)
        
        # Wait for sensor data to be available
        print("Waiting for sensor to provide data...", end="", flush=True)
        while not scd30.scd30.data_available:
            print(".", end="", flush=True)
            time.sleep(0.5)
        print(" done.")
        if args.forced_recal is not None:
            print(f"Ambient pressure is: {scd30.scd30.ambient_pressure} millibar")
            scd30.set_forced_recalibration_reference(args.forced_recal)
        else:
            print(f"Current forced recalibration reference: {scd30.scd30.forced_recalibration_reference} ppm")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
