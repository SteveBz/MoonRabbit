#!/bin/bash

# Check if config.json doesn't exist
if [ ! -f "config.json" ]; then
    cp default_config.json config.json
    echo "Copied default_config.json to config.json. Edit this file with your custom settings."

    # Ensure config.json is in .gitignore
    if ! grep -qxF "config.json" .gitignore 2>/dev/null; then
        echo "config.json" >> .gitignore
        echo "Added config.json to .gitignore"
    fi
else
    echo "config.json already exists. Skipping copy."
fi
