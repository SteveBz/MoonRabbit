# raspberry-pi-scd30-bme280-CO2-monitor-flask-python
A Raspberry Pi powered CO2 monitoring station using Python and Flask  


## Write Up:  

# MoonRabbit
```
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install supervisor -y
sudo cp *.conf /etc/supervisor/conf.d/
sudo apt-get install sqlite3
sudo apt-get install sqlitebrowser

git clone https://github.com/SteveBz/MoonRabbit
cd MoonRabbit/
python3 -m venv venv
. venv/bin/activate
pip3 install flask
pip3 install flask-cors
pip3 install smbus2
pip3 install RPi.bme280
install wheel package??
pip3 install adafruit-blinka
pip3 install adafruit-circuitpython-scd30
pip3 install pandas
pip3 install requests
```

sudo nano /etc/supervisor/supervisord.conf
```
[inet_http_server]
port=*:9001
```
sudo nano /boot/firmware/config.txt
```
# Uncomment some or all of these to enable the optional hardware interfaces
dtparam=i2c_arm=on
#dtparam=i2s=on
dtparam=spi=on

# Set I2C Clock Speed
dtparam=i2c_arm_baudrate=10000
```
