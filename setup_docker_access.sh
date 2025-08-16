#!/bin/bash

# Script to help set up Docker access for the media-bot container

echo "=== Docker Access Setup for Media Bot ==="

# Check if docker group exists
if getent group docker > /dev/null 2>&1; then
    DOCKER_GID=$(getent group docker | cut -d: -f3)
    echo "✅ Docker group found with GID: $DOCKER_GID"
else
    echo "❌ Docker group not found. Please ensure Docker is installed."
    exit 1
fi

# Check if user is in docker group
CURRENT_USER=$(id -un)
if groups $CURRENT_USER | grep -q docker; then
    echo "✅ User $CURRENT_USER is in docker group"
else
    echo "⚠️  User $CURRENT_USER is not in docker group"
    echo "   You may need to add the user to the docker group:"
    echo "   sudo usermod -aG docker $CURRENT_USER"
    echo "   Then log out and back in, or run: newgrp docker"
fi

# Check docker socket permissions
DOCKER_SOCK="/var/run/docker.sock"
if [ -S "$DOCKER_SOCK" ]; then
    echo "✅ Docker socket found at $DOCKER_SOCK"
    SOCK_PERMS=$(stat -c "%a" "$DOCKER_SOCK")
    SOCK_OWNER=$(stat -c "%U:%G" "$DOCKER_SOCK")
    echo "   Permissions: $SOCK_PERMS"
    echo "   Owner: $SOCK_OWNER"
else
    echo "❌ Docker socket not found at $DOCKER_SOCK"
    exit 1
fi

# Export environment variables for docker-compose
export DOCKER_GID=$DOCKER_GID
export CURRENT_UID=$(id -u)

echo ""
echo "=== Environment Variables ==="
echo "CURRENT_UID=$CURRENT_UID"
echo "DOCKER_GID=$DOCKER_GID"
echo ""
echo "You can now run:"
echo "docker-compose up -d"
echo ""
echo "Or set these variables manually:"
echo "export CURRENT_UID=$CURRENT_UID"
echo "export DOCKER_GID=$DOCKER_GID" 