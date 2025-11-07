#!/bin/bash
# Fix Docker Credentials Issue
# This removes the Docker Desktop credential helper that's not available in WSL2

set -e

echo "=========================================="
echo "Fixing Docker Credentials"
echo "=========================================="
echo ""

# Create .docker directory if it doesn't exist
mkdir -p ~/.docker

# Create or update Docker config to not use credential helper
echo "Creating Docker config without credential helper..."
cat > ~/.docker/config.json << 'EOF'
{
  "auths": {}
}
EOF

echo ""
echo "Docker config updated successfully!"
echo ""
echo "Now try running the setup script again:"
echo "  ./setup-services.sh"
echo ""
