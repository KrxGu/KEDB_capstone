#!/bin/bash

# Phase A Quick Start Script
# This script automates the Phase A setup process

set -e  # Exit on any error

echo "Starting Phase A Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Start Docker services
echo -e "${BLUE}Step 1: Starting Docker services...${NC}"
docker compose -f deploy/docker-compose.yml up -d postgres redis meilisearch
echo -e "${GREEN} Services started${NC}"
echo ""

# Step 2: Wait for services to be ready
echo -e "${BLUE}Step 2: Waiting for services to be ready (10 seconds)...${NC}"
sleep 10
echo -e "${GREEN} Services ready${NC}"
echo ""

# Step 3: Check service status
echo -e "${BLUE}Step 3: Checking service status...${NC}"
docker compose -f deploy/docker-compose.yml ps
echo ""

# Step 4: Enable pgvector extension
echo -e "${BLUE}Step 4: Enabling pgvector extension...${NC}"
docker exec -i kedb-postgres psql -U kedb -d kedb << EOF
CREATE EXTENSION IF NOT EXISTS vector;
\dx
EOF
echo -e "${GREEN} pgvector enabled${NC}"
echo ""

# Step 5: Start api server
echo -e "${BLUE}Step 5: Starting API Service...${NC}"
docker compose -f deploy/docker-compose.yml up -d api
echo -e "${GREEN} Service Started${NC}"
echo ""

# Step 6: Apply pregenerated migration
echo -e "${BLUE}Step 6: Applying migration...${NC}"
docker exec -i kedb-api poetry run alembic upgrade head
echo -e "${GREEN} Migration applied${NC}"
echo ""

# Step 7: Verify tables
echo -e "${BLUE}Step 7: Verifying tables were created...${NC}"
TABLE_COUNT=$(docker exec -i kedb-postgres psql -U kedb -d kedb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
echo "Tables created: $TABLE_COUNT (expected: 21)"
if [ "$TABLE_COUNT" -ge 21 ]; then
    echo -e "${GREEN} All tables created successfully${NC}"
else
    echo -e "${RED}⚠️  Warning: Expected 21 tables, got $TABLE_COUNT${NC}"
fi
echo ""

# List all tables
echo -e "${BLUE}Listing all tables:${NC}"
docker exec -i kedb-postgres psql -U kedb -d kedb -c "\dt"
echo ""

# Step 8: Start API
echo -e "${BLUE}Step 8: Starting API server...${NC}"
echo "API will start on http://localhost:8080"
echo ""
echo -e "${GREEN} Phase A setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. API is starting up (this may take a few seconds)"
echo "2. Test the health endpoint: curl http://localhost:8080/api/v1/health"
echo "3. Run tests: docker exec -it kedb-api poetry run pytest tests/test_health.py -v"
echo ""
echo "Starting API server now..."
echo "(Stop Server: docker compose -f deploy/docker-compose.yml down)"
echo ""

docker exec -i kedb-api poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
