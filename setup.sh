#!/bin/bash

# KEDB Platform - Complete Setup Script
# Automates installation for Phase A + B (CRUD API ready)
# Compatible with macOS and Linux

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 KEDB Platform - Automated Setup"
echo "=================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status messages
print_status() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 0: Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION detected"

if ! command_exists poetry; then
    print_error "Poetry is not installed. Install it with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

POETRY_VERSION=$(poetry --version | awk '{print $3}')
print_success "Poetry $POETRY_VERSION detected"

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker daemon is running
if ! docker ps >/dev/null 2>&1; then
    print_warning "Docker daemon is not running. Starting Docker Desktop..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open -a Docker
        print_status "Waiting for Docker to start (max 60 seconds)..."
        for i in {1..30}; do
            if docker ps >/dev/null 2>&1; then
                print_success "Docker is ready"
                break
            fi
            sleep 2
            echo -n "."
        done
        echo ""
    else
        print_error "Please start Docker manually and run this script again."
        exit 1
    fi
fi

print_success "Docker is running"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating default configuration..."
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+asyncpg://kedb:kedb@postgres:5432/kedb
SYNC_DATABASE_URL=postgresql+psycopg://kedb:kedb@postgres:5432/kedb

# For local development (outside Docker)
# DATABASE_URL=postgresql+asyncpg://kedb:kedb@localhost:5432/kedb
# SYNC_DATABASE_URL=postgresql+psycopg://kedb:kedb@localhost:5432/kedb

# Redis Configuration
REDIS_URL=redis://redis:6379/0
RQ_DEFAULT_QUEUE=default

# Meilisearch Configuration
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_MASTER_KEY=local_master_key

# OpenAI Configuration (optional - for Phase D)
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-large

# Server Configuration
UVICORN_HOST=0.0.0.0
UVICORN_PORT=8080
PROJECT_NAME=KEDB Platform
ENVIRONMENT=local
EOF
    print_success ".env file created"
else
    print_success ".env file exists"
fi
echo ""

# Step 1: Install Python dependencies
print_status "Step 1/7: Installing Python dependencies..."
cd backend
poetry install --no-interaction
print_success "Dependencies installed"
echo ""

# Step 2: Start Docker services
print_status "Step 2/7: Starting Docker services (Postgres, Redis, Meilisearch)..."
cd ..

# Use docker-compose or docker compose based on availability
if command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD -f deploy/docker-compose.yml up -d postgres redis meilisearch
print_success "Services started"
echo ""

# Step 3: Wait for PostgreSQL to be ready
print_status "Step 3/7: Waiting for PostgreSQL to be ready..."
echo -n "Checking database connectivity"
for i in {1..30}; do
    if docker exec kedb-postgres pg_isready -U kedb -d kedb >/dev/null 2>&1; then
        echo ""
        print_success "PostgreSQL is ready"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Step 4: Enable pgvector extension
print_status "Step 4/7: Enabling pgvector extension..."
docker exec -i kedb-postgres psql -U kedb -d kedb << 'EOF' >/dev/null 2>&1 || true
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Verify extension
PGVECTOR_CHECK=$(docker exec -i kedb-postgres psql -U kedb -d kedb -t -c "SELECT COUNT(*) FROM pg_extension WHERE extname='vector';")
if [ "$PGVECTOR_CHECK" -ge 1 ]; then
    print_success "pgvector extension enabled"
else
    print_warning "pgvector extension may not be installed"
fi
echo ""

# Step 5: Run database migrations
print_status "Step 5/7: Applying database migrations..."
cd backend

# Check if migration already exists
MIGRATION_COUNT=$(find alembic/versions -name "*.py" -type f 2>/dev/null | wc -l)
if [ "$MIGRATION_COUNT" -eq 0 ]; then
    print_status "Generating initial migration..."
    poetry run alembic revision --autogenerate -m "Initial schema with all tables"
    print_success "Migration generated"
fi

poetry run alembic upgrade head
print_success "Migrations applied"
echo ""

# Step 6: Verify database setup
print_status "Step 6/7: Verifying database setup..."
TABLE_COUNT=$(docker exec -i kedb-postgres psql -U kedb -d kedb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
TABLE_COUNT_TRIMMED=$(echo $TABLE_COUNT | xargs)

echo "   Tables created: $TABLE_COUNT_TRIMMED"

if [ "$TABLE_COUNT_TRIMMED" -ge 21 ]; then
    print_success "All 21+ tables verified"
else
    print_warning "Expected 21 tables, found $TABLE_COUNT_TRIMMED"
fi
echo ""

# Step 7: Display service status
print_status "Step 7/7: Service status..."
$COMPOSE_CMD -f ../deploy/docker-compose.yml ps
echo ""

print_success "========================================="
print_success "🎉 Setup Complete!"
print_success "========================================="
echo ""
echo "Available Services:"
echo "  📊 PostgreSQL:   localhost:5432 (user: kedb, password: kedb, db: kedb)"
echo "  🔴 Redis:        localhost:6379"
echo "  🔍 Meilisearch:  localhost:7700 (master key: local_master_key)"
echo ""
echo "Next Steps:"
echo ""
echo "  1️⃣  Start the API server:"
echo "      cd backend"
echo "      poetry run uvicorn app.main:app --port 8000 --reload"
echo ""
echo "  2️⃣  Test the API:"
echo "      curl http://localhost:8000/api/v1/health"
echo ""
echo "  3️⃣  View API documentation:"
echo "      open http://localhost:8000/docs"
echo ""
echo "  4️⃣  Run tests:"
echo "      cd backend && poetry run pytest tests/ -v"
echo ""
echo "  5️⃣  Stop services when done:"
echo "      $COMPOSE_CMD -f deploy/docker-compose.yml down"
echo ""
