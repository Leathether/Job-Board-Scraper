#!/bin/bash

echo "Installing Chromium and ChromeDriver for VM environment..."

# Update package list
sudo apt update

# Install Chromium (lighter than Chrome, better for VMs)
echo "Installing Chromium..."
sudo apt install -y chromium-browser

# Install ChromeDriver
echo "Installing ChromeDriver..."
sudo apt install -y chromium-chromedriver

# Create symlink if needed
if [ ! -f /usr/bin/chromedriver ]; then
    echo "Creating chromedriver symlink..."
    sudo ln -sf /usr/bin/chromium-chromedriver /usr/bin/chromedriver
fi

# Set permissions
sudo chmod +x /usr/bin/chromium-browser
sudo chmod +x /usr/bin/chromium-chromedriver

echo "Installation complete!"
echo "Chromium should now be available at: /usr/bin/chromium-browser"
echo "ChromeDriver should now be available at: /usr/bin/chromium-chromedriver"

# Test if installation worked
if command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium installation successful"
else
    echo "❌ Chromium installation failed"
fi

if command -v chromedriver &> /dev/null; then
    echo "✅ ChromeDriver installation successful"
else
    echo "❌ ChromeDriver installation failed"
fi 