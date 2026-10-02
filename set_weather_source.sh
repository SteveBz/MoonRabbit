#!/bin/bash
# Usage: sudo ./set_weather_source.sh vantage|ecowitt|none

set -e
SOURCE="$1"

case "$SOURCE" in
    vantage|ecowitt|none) ;;
    *) echo "Usage: $0 vantage|ecowitt|none"; exit 1 ;;
esac

REPO=/home/pi/MoonRabbit
TEMPLATE="$REPO/supervisor/weather-$SOURCE.conf"
TARGET="/etc/supervisor/conf.d/weather.conf"

if [ ! -f "$TEMPLATE" ]; then
    echo "Template not found: $TEMPLATE"
    exit 1
fi

cp "$TEMPLATE" "$TARGET"
sed -i 's/"weather_source": *"[^"]*"/"weather_source": "'"$SOURCE"'"/' "$REPO/config.json"

supervisorctl reread
supervisorctl update
echo "Weather source set to: $SOURCE"
