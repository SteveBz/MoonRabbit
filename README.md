# raspberry-pi-scd30-bme280-CO2-monitor-flask-python
A Raspberry Pi powered CO2 monitoring station using Python and Flask  

# MoonRabbit setup

## Via a keyboard, mouse and screen through the rpi0 OTG port

Connect your keyboard and mouse to the OTG port via a OTG (On-The-Go) USB hub with a micro USB plug. Connect the monitor to the mini-HDMI port and boot by plugging the power cable in.  

### Set up WiFi or Network

Connect to the WiFi using the icon at the top right of the screen.

### Set up SSH & I2C

Menu>Preferences>Praspberry Pi Configuration>Interface>SSH

Menu>Preferences>Praspberry Pi Configuration>Interface>I2C

## Via SSH
### Fix swap memory default
The initial default, virtual memory allocation is very small.  You need to expand it to allow many things, such as updating software.

Run swapon command
```
swapon
> NAME      TYPE  SIZE   USED PRIO
> var/swap file 100M 100M   -2
```
Swap Memory is 100 MB
```
sudo nano /etc/dphys-swapfile
```
Change swap size to 1024 MB
```
CONF_SWAPSIZE=1024
```
Use Control-s to save the changes and control-x to exit nano.
Then reboot Moon Rabbit, to apply the changes.
```
sudo reboot
```
Check swapsize again
```
swapon
> NAME      TYPE  SIZE   USED PRIO
> var/swap file 1024M 377.8M   -2
```
Swap size has changed

### Supervisord

Supervisord allows remore control of the software on the Raspberry Pi Zero 2 W from a browser on the same WiFi LAN.

Install Supervisord
```
# Install necessary packages
sudo apt-get install -y supervisor
# Update and upgrade the system packages
sudo apt-get update && sudo apt-get upgrade -y
# Install necessary packages
sudo apt-get install -y sqlite3 sqlitebrowser
```

# Edit Supervisor configuration to allow web interface
sudo nano /etc/supervisor/supervisord.conf
Add the following lines to enable the web interface
```
[inet_http_server]
port=*:9001
```
Use Control-s to save the changes and control-x to exit nano.
### Enable hardware interfaces in the Raspberry Pi configuration
IIC or I2C (I-squared-C, or I-two-C), is the interface that links all the sensors to the Raspberry Pi Zero 2 W

sudo nano /boot/firmware/config.txt

```
# Uncomment  or add these lines to enable the hardware interfaces

dtparam=i2c_arm=on
#dtparam=i2s=on
dtparam=spi=on

# Set I2C Clock Speed
dtparam=i2c_arm_baudrate=10000
```
Use Control-s to save the changes and control-x to exit nano.
Then reboot Moon Rabbit, to apply the changes.
```
sudo reboot
```
### Install Moon Rabbit Software
```
# Clone the project repository
git clone https://github.com/SteveBz/MoonRabbit
cd MoonRabbit/
# Set up Python virtual environment and activate it
python3 -m venv venv
. venv/bin/activate
# Copy Supervisor configuration files
sudo cp *.conf /etc/supervisor/conf.d/
# Install required Python packages within the virtual environment
pip install flask flask-cors smbus2 RPi.bme280 adafruit-blinka adafruit-circuitpython-scd30 pandas requests
```
Find out the IP address of your raspberry pi from
```
(venv) pi@raspberrypi:~ $ ifconfig | grep 192
        inet 192.168.1.61  netmask 255.255.255.0  broadcast 192.168.1.255
```
And it's the address of the format 192.168, but not ending 255, so in this case its 192.168.1.61

Then reboot Moon Rabbit.
```
sudo reboot
```

### Test Moon Rabbit in a browser
Navigate to a browser, open two tabs and type in the following IP adresesses:
```
<your ip address>:5000
<your ip address>:9001
```
Eg, like this, substituting your address for the example.
```
192.168.1.61:5000
192.168.1.61:9001
```
![Alt text](Screenshot%202024-06-08%20091042.png)
![Alt text](Screenshot%202024-06-08%20091122.png)
