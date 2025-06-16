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

    def set_forced_recalibration_reference(self, value):
        self.scd30.forced_recalibration_reference = value
        print(f"Forced recalibration reference set to {value} ppm")

def main():
    parser = argparse.ArgumentParser(description='SCD30 sensor test.')
    parser.add_argument('-f', '--forced-recal', type=int, help='The forced recalibration reference value in ppm')
    args = parser.parse_args()

    try:
        scd30 = SCD30()
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
