#!/bin/bash
# Fix Docker Credentials for both user and root

set -e

echo "=========================================="
echo "Fixing Docker Credentials (User & Root)"
echo "=========================================="
echo ""

# Fix for current user
echo "Step 1: Fixing Docker config for current user..."
mkdir -p ~/.docker
cat > ~/.docker/config.json << 'EOF'
{
  "auths": {}
}
EOF

# Fix for root (when using sudo)
echo "Step 2: Fixing Docker config for root user..."
sudo mkdir -p /root/.docker
sudo bash -c 'cat > /root/.docker/config.json << "EOF"
{
  "auths": {}
}
EOF'

echo ""
echo "Docker config updated for both user and root!"
echo ""
echo "Now try running the setup script again:"
echo "  ./setup-services.sh"
echo ""
