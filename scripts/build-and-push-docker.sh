#!/bin/bash

################################################################################
# Docker Hub Push Script for Statistics for Strava
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version from composer.json
APP_VERSION=$(grep -o '"version": "[^"]*' composer.json | cut -d'"' -f4 | tail -n1)

echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║   Statistics for Strava - Docker Image Push Script       ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Version: ${GREEN}$APP_VERSION${NC}"
echo ""

# Check if logged in to Docker Hub
echo -e "${YELLOW}Checking Docker Hub login...${NC}"
if ! docker info | grep -q "Username:"; then
    echo -e "${RED}❌ Not logged in to Docker Hub${NC}"
    echo ""
    echo "Please login first:"
    echo "  docker login"
    echo ""
    exit 1
fi

# Get Docker Hub username from login
DOCKER_HUB_USERNAME=$(docker info | grep "Username:" | awk '{print $2}')
echo -e "Logged in as: ${GREEN}$DOCKER_HUB_USERNAME${NC}"
echo ""

# Ask for confirmation
read -p "Continue building and pushing images to Docker Hub as '$DOCKER_HUB_USERNAME'? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting build and push process...${NC}"
echo ""

################################################################################
# Build and Push App Image
################################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📦 Building App Image${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Building app image..."
docker build -f docker/app/Dockerfile -t $DOCKER_HUB_USERNAME/statistics-for-strava:latest .

echo "Tagging with version..."
docker tag $DOCKER_HUB_USERNAME/statistics-for-strava:latest $DOCKER_HUB_USERNAME/statistics-for-strava:v$APP_VERSION

echo "Pushing to Docker Hub..."
docker push $DOCKER_HUB_USERNAME/statistics-for-strava:latest
docker push $DOCKER_HUB_USERNAME/statistics-for-strava:v$APP_VERSION

echo -e "${GREEN}✅ App image pushed successfully!${NC}"
echo ""

################################################################################
# Build and Push CLI Image
################################################################################

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📦 Building CLI Image${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Building CLI image..."
docker build -f docker/php-cli/Dockerfile -t $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest .

echo "Tagging with version..."
docker tag $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest $DOCKER_HUB_USERNAME/statistics-for-strava-cli:v$APP_VERSION

echo "Pushing to Docker Hub..."
docker push $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest
docker push $DOCKER_HUB_USERNAME/statistics-for-strava-cli:v$APP_VERSION

echo -e "${GREEN}✅ CLI image pushed successfully!${NC}"
echo ""

################################################################################
# Summary
################################################################################

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  ✅ PUSH COMPLETE!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Images pushed to Docker Hub:"
echo ""
echo -e "  ${GREEN}Main App Image:${NC}"
echo -e "    • $DOCKER_HUB_USERNAME/statistics-for-strava:latest"
echo -e "    • $DOCKER_HUB_USERNAME/statistics-for-strava:v$APP_VERSION"
echo ""
echo -e "  ${GREEN}CLI Image:${NC}"
echo -e "    • $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest"
echo -e "    • $DOCKER_HUB_USERNAME/statistics-for-strava-cli:v$APP_VERSION"
echo ""
echo -e "🌐 View on Docker Hub: ${BLUE}https://hub.docker.com/u/$DOCKER_HUB_USERNAME${NC}"
echo ""

# Show image sizes
echo "Image sizes:"
echo "  • statistics-for-strava:latest     $(docker image inspect $DOCKER_HUB_USERNAME/statistics-for-strava:latest --format='{{.Size}}' | numfmt --to=iec-i --suffix=B 2>/dev/null || echo 'N/A')"
echo "  • statistics-for-strava-cli:latest $(docker image inspect $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest --format='{{.Size}}' | numfmt --to=iec-i --suffix=B 2>/dev/null || echo 'N/A')"
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Verify images on Docker Hub"
echo "  2. Update README.md with Docker Hub instructions"
echo "  3. Test pulling and running the images"
echo ""
echo "Example pull command:"
echo "  docker pull $DOCKER_HUB_USERNAME/statistics-for-strava:latest"
echo ""