
# Install necessary packages
sudo apt update
sudo apt-get install -y sqlite3 sqlitebrowser

# INDI
sudo apt-get install -y indi-bin indi-aagcloudwatcher-ng
sudo apt install  -y libindi-dev

# NEW: MQTT broker and dev library (replaces pyindi-client)
sudo apt-get install -y mosquitto mosquitto-clients libmosquitto-dev

# Build tools for indi2mqtt
sudo apt-get install -y cmake build-essential


# NEW: build and install indi2mqtt from source
cd /home/pi
if [ ! -d indi2mqtt ]; then
    git clone https://github.com/rkaczorek/indi2mqtt.git
fi
cd indi2mqtt

# Point at the local broker (upstream defaults to a hard-coded IP)
sed -i 's|^#define MQTT_HOST .*|#define MQTT_HOST "localhost"|' indi2mqtt.h

mkdir -p build
cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr ..
make
