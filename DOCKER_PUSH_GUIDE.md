# Docker Hub Image Push Guide

## Overview
This guide explains how to push your Statistics for Strava Docker images to Docker Hub.

## Prerequisites

### 1. Docker Hub Account
- Create an account at [hub.docker.com](https://hub.docker.com)
- Choose a username (e.g., `yourusername`)

### 2. Login to Docker Hub
```bash
# Login to Docker Hub (enter your credentials when prompted)
docker login
```

### 3. Create Repository on Docker Hub
1. Go to [Docker Hub](https://hub.docker.com)
2. Click "Create Repository"
3. Name it: `statistics-for-strava`
4. Set visibility to Public
5. Click "Create"

## Building and Pushing Images

### Option 1: Build and Push Main App Image

```bash
# Build the image with your Docker Hub username
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:latest .

# Tag with version
docker tag yourusername/statistics-for-strava:latest yourusername/statistics-for-strava:v4.7.1

# Push to Docker Hub
docker push yourusername/statistics-for-strava:latest
docker push yourusername/statistics-for-strava:v4.7.1
```

### Option 2: Build and Push CLI Image

```bash
# Build the CLI image
docker build -f docker/php-cli/Dockerfile -t yourusername/statistics-for-strava-cli:latest .

# Tag with version
docker tag yourusername/statistics-for-strava-cli:latest yourusername/statistics-for-strava-cli:v4.7.1

# Push to Docker Hub
docker push yourusername/statistics-for-strava-cli:latest
docker push yourusername/statistics-for-strava-cli:v4.7.1
```

## Automated Build Script

Create a script to automate the build and push process:

```bash
#!/bin/bash
# File: scripts/build-and-push.sh

set -e

# Configuration
DOCKER_HUB_USERNAME="yourusername"
APP_VERSION="v$(grep -o '"version": "[^"]*' composer.json | cut -d'"' -f4 | tail -n1)"

echo "Building and pushing Docker images..."
echo "Version: $APP_VERSION"
echo "Username: $DOCKER_HUB_USERNAME"
echo ""

# Build and push app image
echo "Building app image..."
docker build -f docker/app/Dockerfile -t $DOCKER_HUB_USERNAME/statistics-for-strava:latest .
docker tag $DOCKER_HUB_USERNAME/statistics-for-strava:latest $DOCKER_HUB_USERNAME/statistics-for-strava:$APP_VERSION
docker push $DOCKER_HUB_USERNAME/statistics-for-strava:latest
docker push $DOCKER_HUB_USERNAME/statistics-for-strava:$APP_VERSION

echo ""
echo "Building CLI image..."
docker build -f docker/php-cli/Dockerfile -t $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest .
docker tag $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest $DOCKER_HUB_USERNAME/statistics-for-strava-cli:$APP_VERSION
docker push $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest
docker push $DOCKER_HUB_USERNAME/statistics-for-strava-cli:$APP_VERSION

echo ""
echo "✅ Successfully pushed images to Docker Hub!"
echo "Images:"
echo "  - $DOCKER_HUB_USERNAME/statistics-for-strava:latest"
echo "  - $DOCKER_HUB_USERNAME/statistics-for-strava:$APP_VERSION"
echo "  - $DOCKER_HUB_USERNAME/statistics-for-strava-cli:latest"
echo "  - $DOCKER_HUB_USERNAME/statistics-for-strava-cli:$APP_VERSION"
```

Make it executable and run:
```bash
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh
```

## Using Docker Compose with Hub Images

After pushing, anyone can use your images:

### docker-compose.yml (for users)
```yaml
services:
  app:
    image: yourusername/statistics-for-strava:latest
    container_name: 'statistics-for-strava-app'
    # ... other config

  daemon:
    image: yourusername/statistics-for-strava:latest
    container_name: 'statistics-for-strava-daemon'
    # ... other config

  php-cli:
    image: yourusername/statistics-for-strava-cli:latest
    container_name: 'statistics-for-strava-php-cli'
    # ... other config
```

## Multi-Architecture Build (Optional)

Build for both ARM64 and AMD64:

```bash
# Enable buildx
docker buildx create --use

# Build and push multi-arch image
docker buildx build --platform linux/amd64,linux/arm64 \
  -f docker/app/Dockerfile \
  -t yourusername/statistics-for-strava:latest \
  --push .
```

## GitHub Actions Integration (Optional)

Create `.github/workflows/docker-push.yml`:

```yaml
name: Build and Push Docker Images

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_ACCESS_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_HUB_USERNAME }}/statistics-for-strava
          tags: |
            type=ref,event=tag

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./docker/app/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

## Version Management

### Semantic Versioning
- Use version tags matching your app version (e.g., `v4.7.1`)
- Keep `latest` tag pointing to newest version
- Push both versioned and latest tags

### Version Commands
```bash
# Get current version from composer.json
APP_VERSION=$(grep -o '"version": "[^"]*' composer.json | cut -d'"' -f4 | tail -n1)

# Or manually
APP_VERSION="4.7.1"

# Build with version
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:latest -t yourusername/statistics-for-strava:v$APP_VERSION .
```

## Testing Pulled Images

Test the images others will use:

```bash
# Pull the image
docker pull yourusername/statistics-for-strava:latest

# Run a container
docker run -it --rm yourusername/statistics-for-strava:latest --version
```

## Cleanup

Remove old images from your machine:

```bash
# Remove dangling images
docker image prune

# Remove all images matching pattern
docker images | grep "yourusername/statistics-for-strava" | awk '{print $3}' | xargs docker rmi -f
```

## Troubleshooting

### Build fails with permission errors
```bash
# Try with sudo (Linux/Mac)
sudo docker build -f docker/app/Dockerfile -t username/image:latest .
```

### Push fails with unauthorized error
```bash
# Re-login to Docker Hub
docker logout
docker login --username yourusername
```

### Image too large
```bash
# Check image size
docker images yourusername/statistics-for-strava

# Use multi-stage builds to reduce size
# (Your FrankenPHP image is already optimized)
```

## Documentation

After pushing, update your README.md with:

```markdown
## Docker Deployment

### Using Docker Hub Images

```bash
# Pull images
docker pull yourusername/statistics-for-strava:latest
docker pull yourusername/statistics-for-strava-cli:latest

# Run with docker-compose
docker-compose up -d
```

### Building from Source

```bash
docker build -f docker/app/Dockerfile -t my-statistics-for-strava .
```
```

## Useful Commands Reference

```bash
# Login to Docker Hub
docker login

# Logout from Docker Hub
docker logout

# List your images on Docker Hub
docker search yourusername/statistics-for-strava

# Pull image
docker pull yourusername/statistics-for-strava:latest

# Check image info
docker inspect yourusername/statistics-for-strava:latest

# Build with tag
docker build -f docker/app/Dockerfile -t username/image:tag .

# Push image
docker push username/image:tag

# Tag existing image
docker tag old-tag new-tag

# Remove image locally
docker rmi username/image:tag
```