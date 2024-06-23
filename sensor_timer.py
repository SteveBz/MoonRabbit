from threading import Thread
import time
from datetime import datetime
import signal
import sys
from class_sensor_module import SensorModule

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def periodic_task():
    n=0
    # print ("periodic_task")
    start = time.time()
    start_time = datetime.now()
    while True:
        n=n+1
        #print (f"while True {n}")
        sensor=SensorModule()
        temperature, pressure, humidity, co2, lattitude, longitude = sensor.get_sensor_readings()
        last = time.time()
        logger.info(f"This job started at {start_time} and runs every {round((last-start)/n, 1)} seconds. {n:,}th event")
        time.sleep(10)

if __name__ == '__main__':
    print ("__main__")
    thread = Thread(target=periodic_task)
    thread.start()
