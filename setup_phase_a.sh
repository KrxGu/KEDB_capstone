#!/bin/bash

# Phase A Quick Start Script
# This script automates the Phase A setup process

set -e  # Exit on any error

echo "🚀 Starting Phase A Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Install dependencies
echo -e "${BLUE}Step 1: Installing Python dependencies...${NC}"
cd backend
poetry install
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 2: Start Docker services
echo -e "${BLUE}Step 2: Starting Docker services...${NC}"
cd ..
docker-compose -f deploy/docker-compose.yml up -d postgres redis meilisearch
echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 3: Wait for services to be ready
echo -e "${BLUE}Step 3: Waiting for services to be ready (10 seconds)...${NC}"
sleep 10
echo -e "${GREEN}✅ Services ready${NC}"
echo ""

# Step 4: Check service status
echo -e "${BLUE}Step 4: Checking service status...${NC}"
docker-compose -f deploy/docker-compose.yml ps
echo ""

# Step 5: Enable pgvector extension
echo -e "${BLUE}Step 5: Enabling pgvector extension...${NC}"
docker exec -i kedb-postgres psql -U kedb -d kedb << EOF
CREATE EXTENSION IF NOT EXISTS vector;
\dx
EOF
echo -e "${GREEN}✅ pgvector enabled${NC}"
echo ""

# Step 6: Generate Alembic migration
echo -e "${BLUE}Step 6: Generating Alembic migration...${NC}"
cd backend
poetry run alembic revision --autogenerate -m "Initial schema with all tables"
echo -e "${GREEN}✅ Migration generated${NC}"
echo ""

# Step 7: Apply migration
echo -e "${BLUE}Step 7: Applying migration...${NC}"
poetry run alembic upgrade head
echo -e "${GREEN}✅ Migration applied${NC}"
echo ""

# Step 8: Verify tables
echo -e "${BLUE}Step 8: Verifying tables were created...${NC}"
TABLE_COUNT=$(docker exec -i kedb-postgres psql -U kedb -d kedb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
echo "Tables created: $TABLE_COUNT (expected: 21)"
if [ "$TABLE_COUNT" -ge 21 ]; then
    echo -e "${GREEN}✅ All tables created successfully${NC}"
else
    echo -e "${RED}⚠️  Warning: Expected 21 tables, got $TABLE_COUNT${NC}"
fi
echo ""

# Step 9: List all tables
echo -e "${BLUE}Listing all tables:${NC}"
docker exec -i kedb-postgres psql -U kedb -d kedb -c "\dt"
echo ""

# Step 10: Start API
echo -e "${BLUE}Step 9: Starting API server...${NC}"
echo "API will start on http://localhost:8080"
echo ""
echo -e "${GREEN}✅ Phase A setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. API is starting up (this may take a few seconds)"
echo "2. Test the health endpoint: curl http://localhost:8080/api/v1/health"
echo "3. Run tests: cd backend && poetry run pytest tests/test_health.py -v"
echo ""
echo "Starting API server now..."
echo "(Press Ctrl+C to stop the server)"
echo ""

poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
