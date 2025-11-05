#!/bin/bash
# Database Installation Helper Script for Service-Sense
# This script helps install PostgreSQL, Neo4j, and Redis natively on Ubuntu/Debian

set -e  # Exit on error

echo "=========================================="
echo "Service-Sense Database Installation Helper"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: This script must be run with sudo${NC}"
        echo "Usage: sudo ./scripts/install_databases.sh"
        exit 1
    fi
}

# Function to install PostgreSQL
install_postgresql() {
    echo -e "${YELLOW}Installing PostgreSQL...${NC}"

    apt-get update
    apt-get install -y postgresql postgresql-contrib

    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql

    # Create database and user
    sudo -u postgres psql << EOF
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'service_sense') THEN
      CREATE DATABASE service_sense;
   END IF;

   IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'service_sense') THEN
      CREATE USER service_sense WITH PASSWORD 'testpassword123';
   END IF;

   GRANT ALL PRIVILEGES ON DATABASE service_sense TO service_sense;
END
\$\$;
EOF

    echo -e "${GREEN}✅ PostgreSQL installed and configured${NC}"
    echo "   Database: service_sense"
    echo "   User: service_sense"
    echo "   Password: testpassword123"
    echo ""
}

# Function to install Neo4j
install_neo4j() {
    echo -e "${YELLOW}Installing Neo4j...${NC}"

    # Add Neo4j repository
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
    echo 'deb https://debian.neo4j.com stable latest' | tee /etc/apt/sources.list.d/neo4j.list

    # Install Neo4j
    apt-get update
    apt-get install -y neo4j

    # Set initial password
    neo4j-admin set-initial-password testpassword123

    # Start and enable Neo4j
    systemctl start neo4j
    systemctl enable neo4j

    echo -e "${GREEN}✅ Neo4j installed and configured${NC}"
    echo "   Web interface: http://localhost:7474"
    echo "   Bolt port: 7687"
    echo "   User: neo4j"
    echo "   Password: testpassword123"
    echo ""
}

# Function to install Redis
install_redis() {
    echo -e "${YELLOW}Installing Redis...${NC}"

    apt-get update
    apt-get install -y redis-server

    # Configure password
    echo "requirepass testpassword123" >> /etc/redis/redis.conf

    # Start and enable Redis
    systemctl start redis-server
    systemctl enable redis-server

    echo -e "${GREEN}✅ Redis installed and configured${NC}"
    echo "   Port: 6379"
    echo "   Password: testpassword123"
    echo ""
}

# Function to verify installations
verify_installations() {
    echo -e "${YELLOW}Verifying installations...${NC}"
    echo ""

    # Check PostgreSQL
    if systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}✅ PostgreSQL is running${NC}"
    else
        echo -e "${RED}❌ PostgreSQL is not running${NC}"
    fi

    # Check Neo4j
    if systemctl is-active --quiet neo4j; then
        echo -e "${GREEN}✅ Neo4j is running${NC}"
    else
        echo -e "${RED}❌ Neo4j is not running${NC}"
    fi

    # Check Redis
    if systemctl is-active --quiet redis-server; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${RED}❌ Redis is not running${NC}"
    fi

    echo ""
}

# Main menu
show_menu() {
    echo "What would you like to install?"
    echo "1) All databases (PostgreSQL + Neo4j + Redis)"
    echo "2) PostgreSQL only"
    echo "3) Neo4j only"
    echo "4) Redis only"
    echo "5) Verify existing installations"
    echo "6) Exit"
    echo ""
    read -p "Enter your choice [1-6]: " choice
}

# Main execution
main() {
    check_root

    show_menu

    case $choice in
        1)
            install_postgresql
            install_neo4j
            install_redis
            verify_installations
            ;;
        2)
            install_postgresql
            ;;
        3)
            install_neo4j
            ;;
        4)
            install_redis
            ;;
        5)
            verify_installations
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}=========================================="
    echo "Installation complete!"
    echo "==========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: python scripts/init_databases.py    # Initialize database schemas"
    echo "2. Run: python scripts/load_data.py          # Load Seattle Open Data"
    echo "3. Start the API: ./start_api.sh"
    echo ""
}

main
