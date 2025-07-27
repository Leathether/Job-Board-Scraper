#!/bin/bash

echo "Installing all dependencies for LinkedIn Job Scraper..."

# Update package list
sudo apt update

# Install Chromium and ChromeDriver
echo "Installing Chromium and ChromeDriver..."
sudo apt install -y chromium-browser chromium-chromedriver

# Install X11 dependencies for virtual display
echo "Installing X11 dependencies for virtual display..."
sudo apt install -y xvfb x11-utils xauth

# Install additional dependencies that might be needed
echo "Installing additional dependencies..."
sudo apt install -y libxss1 libappindicator1 libindicator7

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
echo "X11 virtual display support is now available"

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

if command -v xvfb &> /dev/null; then
    echo "✅ X11 virtual display support successful"
else
    echo "❌ X11 virtual display support failed"
fi 