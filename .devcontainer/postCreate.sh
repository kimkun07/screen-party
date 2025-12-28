#!/usr/bin/env bash
set -e

echo "▶ postCreate start"

echo 'source /workspaces/screen-party/.venv/bin/activate' >> ~/.bashrc

npm install -g happy-coder

echo "▶ postCreate done"
