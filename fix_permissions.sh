#!/bin/bash

# Script to fix permissions for ComfyUI directories

echo "=== Fixing ComfyUI Directory Permissions ==="

# Get current user and docker group info
CURRENT_UID=$(id -u)
DOCKER_GID=$(getent group docker | cut -d: -f3)

if [ -z "$DOCKER_GID" ]; then
    echo "❌ Docker group not found. Please ensure Docker is installed."
    exit 1
fi

echo "Current user UID: $CURRENT_UID"
echo "Docker group GID: $DOCKER_GID"

# Create directories if they don't exist
sudo mkdir -p /storage/comfyui/input /storage/comfyui/output

# Set ownership to current user and docker group
echo "Setting ownership of ComfyUI directories..."
sudo chown -R $CURRENT_UID:$DOCKER_GID /storage/comfyui/input /storage/comfyui/output

# Set permissions
echo "Setting permissions..."
sudo chmod -R 755 /storage/comfyui/input /storage/comfyui/output

# Verify the changes
echo ""
echo "=== Verification ==="
echo "Input directory:"
ls -la /storage/comfyui/input
echo ""
echo "Output directory:"
ls -la /storage/comfyui/output

echo ""
echo "✅ Permissions fixed successfully!"
echo "You can now rebuild and restart the bot container:"
echo "docker compose down"
echo "docker compose up --build -d" 