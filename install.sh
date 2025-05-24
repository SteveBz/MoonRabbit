# Install necessary packages
sudo apt update
sudo apt-get install -y sqlite3 sqlitebrowser
sudo apt install -y software-properties-common
sudo apt-get install -y indi-bin indi-aagcloudwatcher-ng
sudo apt install  -y swig
sudo apt install  -y libindi-dev

# Clear supervisor configuration files
sudo rm /etc/supervisor/conf.d/*.conf
# Copy new Supervisor configuration files
sudo cp *.conf /etc/supervisor/conf.d/
# Install required Python packages within the virtual environment
pip3 install flask flask-cors smbus2 RPi.bme280 adafruit-blinka==8.40.0 adafruit-circuitpython-scd30 pandas requests psutil

sudo apt-get update
sudo apt-get install libdbus-1-dev pkg-config cmake
sudo apt-get install libglib2.0-dev
pip install pyindi-client --no-cache-dir

sudo apt-get -y autoremove
sudo reboot
