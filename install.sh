#!/bin/bash

# PT Manager Pro Installation Script

set -e

echo "=========================================="
echo "  PT Manager Pro Installation"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Generate random secret key if not set
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -hex 32)
    echo "Generated SECRET_KEY: $SECRET_KEY"
    echo "Save this key for future reference!"
fi

# Create data directory
mkdir -p data

# Build and start containers
echo "Building containers..."
if docker compose version &> /dev/null; then
    docker compose build
    docker compose up -d
else
    docker-compose build
    docker-compose up -d
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "PT Manager Pro is now running at: http://localhost:8080"
echo ""
echo "On first visit, you will be prompted to create an admin account."
echo ""
echo "To stop the application:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
