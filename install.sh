#!/bin/bash
# Interactive Installation Helper for Service-Sense
# Guides you through the complete installation process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Clear screen
clear

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          SERVICE-SENSE AI TRIAGE SYSTEM                          ║
║          Complete Installation Helper                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${CYAN}This script will install everything needed for the full system:${NC}"
echo ""
echo "  🦙 Ollama + llama3.1:8b (FREE local LLM)"
echo "  📊 PostgreSQL (structured data)"
echo "  🔗 Neo4j (graph database)"
echo "  ⚡ Redis (caching)"
echo "  🚀 Initialize and start all services"
echo ""
echo -e "${YELLOW}Time required: 15-20 minutes${NC}"
echo -e "${YELLOW}Internet required: Yes (downloading ~8GB)${NC}"
echo -e "${YELLOW}Sudo access required: Yes${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}❌ Do not run this script with sudo!${NC}"
    echo -e "${YELLOW}This script will ask for sudo when needed.${NC}"
    echo ""
    echo "Run it as:"
    echo "  ./install.sh"
    exit 1
fi

# Prompt to continue
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
read -p "Ready to proceed with installation? [y/N] " -n 1 -r
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled.${NC}"
    echo ""
    echo "When ready, run: ./install.sh"
    exit 0
fi

echo ""
echo -e "${GREEN}🚀 Starting installation...${NC}"
echo ""
sleep 2

# Step 1: System installation
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  STEP 1 of 2: Install System Components                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}This will install:${NC}"
echo "  • Ollama (local LLM engine)"
echo "  • llama3.1:8b model (~4.7GB)"
echo "  • PostgreSQL"
echo "  • Neo4j"
echo "  • Redis"
echo ""
echo -e "${YELLOW}⏱️  Estimated time: 10-15 minutes${NC}"
echo -e "${YELLOW}🔐 You will be prompted for your sudo password${NC}"
echo ""

read -p "Press Enter to continue..."
echo ""

# Run installation script
if sudo ./scripts/install_all.sh; then
    echo ""
    echo -e "${GREEN}✅ Step 1 completed successfully!${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Step 1 failed!${NC}"
    echo ""
    echo "Check the error messages above."
    echo "For troubleshooting, see: INSTALL_GUIDE.md"
    exit 1
fi

sleep 3

# Step 2: Initialize and start
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  STEP 2 of 2: Initialize Databases and Start Services           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}This will:${NC}"
echo "  • Create database schemas"
echo "  • Start Ollama server"
echo "  • Verify all databases"
echo "  • Start API server with full features"
echo ""
echo -e "${YELLOW}⏱️  Estimated time: 3-5 minutes${NC}"
echo -e "${GREEN}✓ No sudo required for this step${NC}"
echo ""

read -p "Press Enter to continue..."
echo ""

# Run setup script
if ./scripts/setup_after_install.sh; then
    echo ""
    echo -e "${GREEN}✅ Step 2 completed successfully!${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Step 2 failed!${NC}"
    echo ""
    echo "Check the error messages above."
    echo "For troubleshooting, see: INSTALL_GUIDE.md"
    exit 1
fi

sleep 2

# Success banner
clear
echo -e "${GREEN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                  ✅ INSTALLATION COMPLETE! ✅                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Your Service-Sense AI Triage System is now running!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}📊 Service Status:${NC}"
echo ""
echo "  🚀 API Gateway:    http://localhost:8000"
echo "  🦙 Ollama LLM:     http://localhost:11434"
echo "  🔗 Neo4j Browser:  http://localhost:7474"
echo "  📊 PostgreSQL:     localhost:5432"
echo "  ⚡ Redis:          localhost:6379"
echo "  🗄️  ChromaDB:       data/chroma/"
echo ""

echo -e "${BLUE}🧪 Quick Test:${NC}"
echo ""
echo "Try this command to test your system:"
echo ""
echo -e "${YELLOW}curl -X POST http://localhost:8000/api/v2/triage \\
  -H \"Content-Type: application/json\" \\
  -d '{\"text\": \"There is a pothole on 5th Avenue\"}' | python3 -m json.tool${NC}"
echo ""

echo -e "${BLUE}📚 Documentation:${NC}"
echo ""
echo "  • SETUP_COMPLETE.md       - Overview and next steps"
echo "  • INSTALL_GUIDE.md        - Detailed guide and troubleshooting"
echo "  • DATABASE_STATUS.md      - Database information"
echo "  • OLLAMA_INTEGRATION.md   - LLM provider guide"
echo "  • API Docs: http://localhost:8000/docs"
echo ""

echo -e "${BLUE}🎯 What You Can Do Now:${NC}"
echo ""
echo "  1. Test the API (see Quick Test above)"
echo "  2. Load Seattle Open Data: python scripts/load_data.py"
echo "  3. Train ML models: python ml/training/train_models.py"
echo "  4. Explore the interactive API docs: http://localhost:8000/docs"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Thank you for installing Service-Sense!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
