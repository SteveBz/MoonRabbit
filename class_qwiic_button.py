from __future__ import print_function
import qwiic_button   # pip3 install sparkfun-qwiic-button
import time
from datetime import datetime
import sys
import subprocess

def button_monitor():

    print("\nSparkFun Qwiic Button Example 1")
    stop_button = qwiic_button.QwiicButton()

    if stop_button.begin() == False:
        print("\nThe Qwiic Button isn't connected to the system. Please check your connection", \
            file=sys.stderr)
        return
        
    stop_button.LED_off()   
    print(datetime.now(), "Button ready!")
    stop_button.is_pressed=False
    time.sleep(1)
    while True:
        stop_button.LED_on(4)  
        print(stop_button.is_button_pressed())  
        if stop_button.is_button_pressed() == True:
            print("\nThe stop button is pressed!")
            stop_button.LED_off()   
            stop_button.clear_event_bits() 
            shut_down()
        time.sleep(0.1)

# modular function to shutdown Pi
def shut_down():
    print("shutting down")
    command="ls"
    # command = "/usr/bin/sudo /sbin/shutdown -h now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)



if __name__ == '__main__':
    time.sleep(1)
    try:
        button_monitor()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("\nEnding Example 1")
        sys.exit(0)
