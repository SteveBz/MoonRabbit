# raspberry-pi-scd30-bme280-CO2-monitor-flask-python
A Raspberry Pi powered CO2 monitoring station using Python and Flask  

# MoonRabbit

## Set up WiFi or Network

## Set up SSH

## Via SSH
## Fix swap memory default
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
Reboot
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

Install Supervisord
```
# Install necessary packages
sudo apt-get install -y supervisor 
# Copy Supervisor configuration files
sudo cp *.conf /etc/supervisor/conf.d/
# Edit Supervisor configuration to allow web interface
sudo nano /etc/supervisor/supervisord.conf
```

Add the following lines to enable the web interface
```
[inet_http_server]
port=*:9001
```

## Enable hardware interfaces in the Raspberry Pi configuration
sudo nano /boot/firmware/config.txt

```
# Uncomment  or add these lines to enable the hardware interfaces

dtparam=i2c_arm=on
#dtparam=i2s=on
dtparam=spi=on

# Set I2C Clock Speed
dtparam=i2c_arm_baudrate=10000
```

## Install Software
```
# Update and upgrade the system packages
sudo apt-get update && sudo apt-get upgrade -y
# Install necessary packages
sudo apt-get install -y supervisor sqlite3 sqlitebrowser
# Clone the project repository
git clone https://github.com/SteveBz/MoonRabbit
cd MoonRabbit/
# Set up Python virtual environment and activate it
python3 -m venv venv
. venv/bin/activate
# Install required Python packages within the virtual environment
pip install flask flask-cors smbus2 RPi.bme280 adafruit-blinka adafruit-circuitpython-scd30 pandas requests
# Copy Supervisor configuration files
sudo cp *.conf /etc/supervisor/conf.d/
```

