#!/bin/bash
echo "Resetting LlamaCag UI settings..."
# Remove configuration files
rm -f ~/.llamacag/config.json
rm -f ~/.llamacag/cache_registry.json
rm -f ~/.llamacag/usage_registry.json
# Create fresh .env file
cp .env.example .env
echo "Settings reset. The application will start fresh on next run."