#!/bin/bash

# Function to handle file setup
setup_config() {
    local default_file="$1"
    local target_file="$2"
    local message="${3:-Edit this file with your custom settings}"

    # Create file if it doesn't exist
    if [ ! -f "$target_file" ]; then
        if [ ! -f "$default_file" ]; then
            echo "Error: Default file $default_file not found!" >&2
            return 1
        fi
        
        cp "$default_file" "$target_file"
        echo "Copied $default_file to $target_file. $message"
        
        # Add to .gitignore if not already present
        if ! grep -qxF "$target_file" .gitignore 2>/dev/null; then
            echo "$target_file" >> .gitignore
            echo "Added $target_file to .gitignore"
        fi
        return 0
    fi
    return 2
}

# Process config files
setup_config "default_config.json" "config.json"
setup_config "default_sensor_value.json" "sensor_values.json" "Edit this file with your sensor values"

# Final status report
if [ $? -ne 2 ]; then  # Only show if at least one file was created
    echo -e "\nRemember to edit the configuration files before use!"
fi

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
