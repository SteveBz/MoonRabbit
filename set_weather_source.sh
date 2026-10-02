#!/bin/bash
# Usage: sudo ./set_weather_source.sh vantage|ecowitt|none
set -e

SOURCE="$1"
case "$SOURCE" in
    vantage|ecowitt|none) ;;
    *) echo "Usage: $0 vantage|ecowitt|none"; exit 1 ;;
esac

REPO=/home/pi/MoonRabbit
TEMPLATE="$REPO/weather-$SOURCE.conf"
TARGET="/etc/supervisor/conf.d/weather.conf"

if [ ! -f "$TEMPLATE" ]; then
    echo "Template not found: $TEMPLATE"
    exit 1
fi

sudo cp "$TEMPLATE" "$TARGET"

# Update config.json
python3 - <<PY
import json
p = "$REPO/config.json"
with open(p) as f:
    c = json.load(f)
c["weather_source"] = "$SOURCE"
with open(p, "w") as f:
    json.dump(c, f, indent=4)
PY

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart SensorTimer
echo "Weather source set to: $SOURCE"
