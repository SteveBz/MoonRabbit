
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
