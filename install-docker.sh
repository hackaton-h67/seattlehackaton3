#!/bin/bash
# Docker Installation Script for WSL2
# This script will install Docker and Docker Compose on your WSL2 environment

set -e

echo "=========================================="
echo "Docker Installation for WSL2"
echo "=========================================="
echo ""

# Update package index
echo "Step 1: Updating package index..."
sudo apt-get update

# Install prerequisites
echo ""
echo "Step 2: Installing prerequisites..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo ""
echo "Step 3: Adding Docker's official GPG key..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
echo ""
echo "Step 4: Setting up Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
echo ""
echo "Step 5: Updating package index with Docker repo..."
sudo apt-get update

# Install Docker Engine, CLI, and Docker Compose
echo ""
echo "Step 6: Installing Docker Engine, CLI, and Docker Compose..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker service
echo ""
echo "Step 7: Starting Docker service..."
sudo service docker start

# Add current user to docker group (optional, allows running docker without sudo)
echo ""
echo "Step 8: Adding user to docker group..."
sudo usermod -aG docker $USER

echo ""
echo "=========================================="
echo "Docker Installation Complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: You may need to:"
echo "1. Log out and log back in for group changes to take effect"
echo "2. Or run: newgrp docker"
echo "3. Verify installation: docker --version"
echo ""
echo "To start Docker service in the future, run:"
echo "  sudo service docker start"
echo ""
