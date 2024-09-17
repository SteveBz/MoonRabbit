# Install necessary packages
sudo apt update
sudo apt-get install -y sqlite3 sqlitebrowser
sudo apt install -y software-properties-common
sudo apt-get install -y indi-bin indi-aagcloudwatcher-ng
sudo apt install swig
sudo apt install libindi-dev

# Clear supervisor configuration files
sudo rm /etc/supervisor/conf.d/*.conf
# Copy new Supervisor configuration files
sudo cp *.conf /etc/supervisor/conf.d/
# Install required Python packages within the virtual environment
pip3 install flask flask-cors smbus2 RPi.bme280 adafruit-blinka adafruit-circuitpython-scd30 pandas requests psutil

sudo apt-get -y autoremove
