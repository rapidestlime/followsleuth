#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Specify the Python version you want to install
PYTHON_VERSION=3.11.1

# Install pyenv if not already installed
if ! command -v pyenv &> /dev/null; then
    echo "pyenv not found. Installing pyenv..."
    curl https://pyenv.run | bash

    # Add pyenv to bashrc to make it available in the shell
    export PATH="$HOME/.pyenv/bin:$PATH"
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc
    source ~/.bashrc
fi

# Install the specified Python version
echo "Installing Python $PYTHON_VERSION..."
pyenv install -s $PYTHON_VERSION

# Create a new virtual environment using the specified Python version
echo "Creating virtual environment..."
pyenv virtualenv $PYTHON_VERSION myenv

# Activate the virtual environment
echo "Activating virtual environment..."
pyenv activate followsleuth

# Install requirements from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "requirements.txt not found. Skipping package installation."
fi

echo "Setup complete. To activate the virtual environment, run 'pyenv activate followsleuth'."