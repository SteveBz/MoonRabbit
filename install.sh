# Sync datetime
sudo timedatectl set-ntp true

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

# REMOVED: swig, libdbus-1-dev, pkg-config, libglib2.0-dev
#          (these were only needed for pyindi-client)

# Make sure the broker runs on boot
sudo systemctl enable --now mosquitto

# Clear supervisor configuration files
sudo rm /etc/supervisor/conf.d/*.conf
# Copy new Supervisor configuration files
sudo cp *.conf /etc/supervisor/conf.d/

# Install required Python packages within the virtual environment
pip3 install flask flask-cors smbus2 RPi.bme280 adafruit-blinka==8.40.0 adafruit-circuitpython-scd30 pandas requests psutil pandas sqlalchemy  paho-mqtt


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

# REMOVED: pyindi-client install
# pip install pyindi-client --no-cache-dir

sudo apt-get update
#sudo apt-get install -y libdbus-1-dev pkg-config cmake
#sudo apt-get install  -y libglib2.0-dev

# --------------------------------------------------------------------------
# Allow the SensorModule user (pi) to restart indi2mqtt via supervisorctl
# without a password. Required by the MQTT staleness watchdog in
# class_sensor_module.py.
#
# Idempotent: writes to a fixed file in /etc/sudoers.d/. Re-running replaces
# the file with identical content rather than appending a second rule.
# --------------------------------------------------------------------------
SUDOERS_FILE="/etc/sudoers.d/sensor-restart-indi2mqtt"
SUPERVISORCTL="$(command -v supervisorctl)"
SENSOR_USER="${SUDO_USER:-pi}"

if [ -z "$SUPERVISORCTL" ]; then
    echo "WARNING: supervisorctl not found — skipping sudoers rule"
else
    EXPECTED_RULE="$SENSOR_USER ALL=(ALL) NOPASSWD: $SUPERVISORCTL restart indi2mqtt"

    # If the file already contains the exact rule, do nothing.
    if [ -f "$SUDOERS_FILE" ] && grep -qF -- "$EXPECTED_RULE" "$SUDOERS_FILE"; then
        echo "Sudoers rule already installed: $SUDOERS_FILE"
    else
        echo "Installing sudoers rule: $SENSOR_USER may restart indi2mqtt"

        TMP_SUDOERS=$(mktemp)
        cat > "$TMP_SUDOERS" <<EOF
# Allow the SensorModule process to restart indi2mqtt without a password.
# Installed by MoonRabbit install.sh
$EXPECTED_RULE
EOF

        if visudo -cf "$TMP_SUDOERS" >/dev/null 2>&1; then
            install -m 0440 -o root -g root "$TMP_SUDOERS" "$SUDOERS_FILE"
            echo "  Installed: $SUDOERS_FILE"
        else
            echo "  ERROR: sudoers syntax check failed — not installing"
            cat "$TMP_SUDOERS"
        fi
        rm -f "$TMP_SUDOERS"
    fi
fi

sudo apt-get -y autoremove
sudo reboot
