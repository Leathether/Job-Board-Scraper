#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    print("Starting LinkedIn Job Scraper Backend Server...")
    
    # Get the backend directory
    backend_dir = Path(__file__).parent
    venv_path = backend_dir / "venv"
    
    # Check if we're in the right directory
    if not (backend_dir / "server.py").exists():
        print("Error: server.py not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Remove existing venv if it's corrupted
    if venv_path.exists():
        print("Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create virtual environment
    print("Creating virtual environment...")
    try:
        # Use python3 -m venv instead of venv.create() for better reliability
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)
    
    # Get the pip and python paths
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Ensure pip is available
    print("Ensuring pip is available...")
    try:
        # Use ensurepip to install pip
        subprocess.run([str(python_path), "-m", "ensurepip", "--upgrade"], 
                      check=True, cwd=backend_dir)
        print("Pip ensured successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error ensuring pip: {e}")
        sys.exit(1)
    
    # Install requirements
    print("Installing Python requirements...")
    try:
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], 
                      check=True, cwd=backend_dir)
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)
    
    # Start the server
    print("Starting FastAPI server on port 8000...")
    try:
        subprocess.run([str(python_path), "server.py"], 
                      check=True, cwd=backend_dir)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main() 