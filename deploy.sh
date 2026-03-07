#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Arthor Agent Deployment Script ===${NC}"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: docker could not be found. Please install Docker first."
    exit 1
fi

# 1. Environment Setup
if [ ! -f .env ]; then
    echo -e "${BLUE}[1/4] Creating .env from template...${NC}"
    cp .env.example .env
    # Generate a random secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/change-me-in-production/$(openssl rand -hex 32)/" .env
    else
        sed -i "s/change-me-in-production/$(openssl rand -hex 32)/" .env
    fi
    echo "  > Created .env with generated secret key."
else
    echo -e "${BLUE}[1/4] Using existing .env file.${NC}"
fi

# 2. Select LLM Mode
echo -e "${BLUE}[2/4] Selecting LLM Provider...${NC}"
if grep -q "LLM_PROVIDER=openai" .env; then
    echo "  > Detected OpenAI configuration."
    COMPOSE_FILES="-f docker-compose.yml"
else
    echo "  > Using Local LLM (Ollama)."
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.ollama.yml"
fi

# 3. Build and Start Services
echo -e "${BLUE}[3/4] Building and starting services...${NC}"
echo "  > This may take a few minutes..."
docker compose $COMPOSE_FILES up -d --build

# 4. Post-Start Setup (Ollama only)
if [[ "$COMPOSE_FILES" == *"ollama"* ]]; then
    echo -e "${BLUE}[4/4] Checking Ollama model...${NC}"
    # Wait for Ollama to be ready
    echo "  > Waiting for Ollama service..."
    sleep 5
    
    # Pull default model if not exists
    MODEL=$(grep OLLAMA_MODEL .env | cut -d '=' -f2 || echo "llama2")
    echo "  > Ensuring model '$MODEL' is available..."
    docker compose exec ollama ollama pull $MODEL
fi

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "Access your services at:"
echo -e "  - Dashboard: http://localhost:8501"
echo -e "  - API Docs:  http://localhost:8000/docs"
