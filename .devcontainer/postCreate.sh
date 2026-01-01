#!/usr/bin/env bash
set -e

echo "▶ postCreate start"

# Install happy-coder (should be first on postCreate script)
if command -v npm &> /dev/null; then
    echo "▶ Installing happy-coder..."
    npm install -g happy-coder
fi

# Install uv
echo "▶ Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Create .venv and install dependencies using uv
echo "▶ Creating venv and installing dependencies..."
cd /workspaces/screen-party
uv venv
uv sync --all-groups

# Add venv activation to bashrc
if ! grep -q "source /workspaces/screen-party/.venv/bin/activate" ~/.bashrc; then
    echo 'source /workspaces/screen-party/.venv/bin/activate' >> ~/.bashrc
fi

echo "▶ postCreate done"
