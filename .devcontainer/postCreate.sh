#!/usr/bin/env bash
set -e

echo "▶ postCreate start"

# Install happy-coder (should be first on postCreate script)
if command -v npm &> /dev/null; then
    echo "▶ Installing happy-coder..."
    npm install -g happy-coder@0.13.0
    # Playstore version 1.5.0
    # happy-server version kimkun07/happy-server-selfhost:v0.2.0
fi

# Install PyQt6 system dependencies for headless testing
echo "▶ Installing PyQt6 system dependencies..."
apt-get update > /dev/null 2>&1
apt-get install -y --no-install-recommends \
  libgl1 \
  libxkbcommon-x11-0 \
  libdbus-1-3 \
  libegl1 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-randr0 \
  libxcb-render-util0 \
  libxcb-shape0 \
  libxcb-xinerama0 \
  libxcb-xfixes0 \
  libxcb-cursor0 \
  > /dev/null 2>&1

# Install uv
echo "▶ Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create .venv and install dependencies using uv
echo "▶ Creating venv and installing dependencies..."
cd /workspaces/screen-party
uv venv --clear
uv sync --all-groups

# Add venv activation to bashrc
if ! grep -q "source /workspaces/screen-party/.venv/bin/activate" ~/.bashrc; then
    echo 'source /workspaces/screen-party/.venv/bin/activate' >> ~/.bashrc
fi

echo "▶ postCreate done"
