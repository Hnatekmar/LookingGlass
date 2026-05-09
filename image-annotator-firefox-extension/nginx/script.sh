#!/bin/bash

# Image Annotator - Nginx Reverse Proxy Startup Script
# Runs nginx reverse proxy on port 9090 pointing to 172.16.100.174:8000

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="172.16.100.174:8000"
FRONTEND_PORT="9090"

echo "============================================================"
echo "  Image Annotator - Nginx Reverse Proxy"
echo "============================================================"
echo ""
echo "  Backend:  http://${BACKEND}"
echo "  Frontend: http://localhost:${FRONTEND_PORT}"
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running"
    exit 1
fi

# Check if docker compose is available
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Error: Docker Compose is not installed"
    exit 1
fi

echo "✓ Docker is running"
echo "✓ Using: ${COMPOSE_CMD}"
echo ""

# Navigate to script directory
cd "${SCRIPT_DIR}"

# Check if nginx.conf exists
if [ ! -f "nginx.conf" ]; then
    echo "❌ Error: nginx.conf not found in ${SCRIPT_DIR}"
    exit 1
fi

# Update nginx.conf with correct port if needed
if ! grep -q "listen ${FRONTEND_PORT};" nginx.conf 2>/dev/null; then
    # Port is configured in docker-compose.yml, not nginx.conf
    echo "✓ Configuration ready"
fi

# Check if container is already running
if ${COMPOSE_CMD} ps | grep -q "image-annotator-proxy"; then
    echo "⚠️  Container is already running"
    echo ""
    echo "To restart: ${COMPOSE_CMD} restart"
    echo "To stop:    ${COMPOSE_CMD} down"
    exit 0
fi

# Start the container
echo "🚀 Starting nginx reverse proxy..."
echo ""

${COMPOSE_CMD} up -d

# Wait for container to be ready
echo ""
echo "⏳ Waiting for nginx to start..."
sleep 2

# Check if container is running
if ${COMPOSE_CMD} ps | grep -q "Up"; then
    echo ""
    echo "============================================================"
    echo "  ✓ Nginx Reverse Proxy Started Successfully"
    echo "============================================================"
    echo ""
    echo "  Frontend: http://localhost:${FRONTEND_PORT}"
    echo "  Backend:  http://${BACKEND}"
    echo ""
    echo "  Test: curl http://localhost:${FRONTEND_PORT}/health"
    echo ""
    echo "  Logs:   ${COMPOSE_CMD} logs -f"
    echo "  Stop:   ${COMPOSE_CMD} down"
    echo ""
else
    echo ""
    echo "❌ Error: Container failed to start"
    echo ""
    echo "Check logs: ${COMPOSE_CMD} logs"
    exit 1
fi
