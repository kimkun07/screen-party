#!/usr/bin/env bash
set -e

echo "▶ postCreate start"

# Install happy-coder
npm install -g happy-coder

# Create .venv-linux and install dependencies
echo "▶ Creating .venv-linux..."
python -m venv /workspaces/screen-party/.venv-linux

echo "▶ Installing dependencies..."
source /workspaces/screen-party/.venv-linux/bin/activate

# Install pip requirements
python -m pip install --upgrade pip
pip install -r /workspaces/screen-party/pip-requirements.txt
pip install -r /workspaces/screen-party/dev-requirements.txt

# Install server and client packages in editable mode
pip install -e /workspaces/screen-party/server
pip install -r /workspaces/screen-party/client/requirements.txt

# Add venv activation to bashrc
echo 'source /workspaces/screen-party/.venv-linux/bin/activate' >> ~/.bashrc

echo "▶ postCreate done"
