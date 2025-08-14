#!/bin/bash

echo "Testing installer file paths..."
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

echo ""
echo "Checking if analytics files exist:"
if [ -f "analytics/sre_analytics_engine.py" ]; then
    echo "✓ sre_analytics_engine.py exists"
else
    echo "✗ sre_analytics_engine.py missing"
fi

if [ -f "analytics/alert_correlation.py" ]; then
    echo "✓ alert_correlation.py exists"
else
    echo "✗ alert_correlation.py missing"
fi

if [ -f "analytics/README.md" ]; then
    echo "✓ analytics README.md exists"
else
    echo "✗ analytics README.md missing"
fi

echo ""
echo "Checking if API files exist:"
if [ -f "nagprom_rest_api.py" ]; then
    echo "✓ nagprom_rest_api.py exists"
else
    echo "✗ nagprom_rest_api.py missing"
fi

if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt exists"
else
    echo "✗ requirements.txt missing"
fi

if [ -f "nagprom-api.service" ]; then
    echo "✓ nagprom-api.service exists"
else
    echo "✗ nagprom-api.service missing"
fi

if [ -f "apache-nagprom.conf" ]; then
    echo "✓ apache-nagprom.conf exists"
else
    echo "✗ apache-nagprom.conf missing"
fi

if [ -f "fix-dependencies.sh" ]; then
    echo "✓ fix-dependencies.sh exists"
else
    echo "✗ fix-dependencies.sh missing"
fi

echo ""
echo "Testing if install.sh is executable:"
if [ -x "install.sh" ]; then
    echo "✓ install.sh is executable"
else
    echo "✗ install.sh is not executable"
    echo "Making it executable..."
    chmod +x install.sh
fi
