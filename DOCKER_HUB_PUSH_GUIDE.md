# Docker Hub Push Guide

## Prerequisites

1. **Docker Hub Account**: Create an account at [hub.docker.com](https://hub.docker.com)
2. **Docker CLI**: Ensure Docker is installed and running
3. **Repository**: Create a repository on Docker Hub (e.g., `yourusername/statistics-for-strava`)

## Method 1: Using Docker CLI Directly

### Step 1: Log in to Docker Hub
```bash
docker login
```
Enter your Docker Hub username and password when prompted.

### Step 2: Build the Docker Image
```bash
# Build the app image
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:latest .

# Or with specific tag
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:v1.0.0 .
```

### Step 3: Push to Docker Hub
```bash
docker push yourusername/statistics-for-strava:latest
docker push yourusername/statistics-for-strava:v1.0.0
```

## Method 2: Using Docker Compose (Recommended)

### Build and Tag
```bash
# Build with custom tag
docker-compose build app

# Tag the built image
docker tag statistics-for-strava-app:latest yourusername/statistics-for-strava:latest
```

### Push to Docker Hub
```bash
docker push yourusername/statistics-for-strava:latest
```

## Method 3: Using GitHub Actions (Automated)

Create `.github/workflows/docker-push.yml`:

```yaml
name: Build and Push to Docker Hub

on:
  push:
    tags:
      - 'v*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
        
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}
          
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./docker/app/Dockerfile
          push: true
          tags: |
            yourusername/statistics-for-strava:latest
            yourusername/statistics-for-strava:${{ github.ref_name }}
```

### Setting up GitHub Secrets
1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Add secrets:
   - `DOCKER_HUB_USERNAME`: Your Docker Hub username
   - `DOCKER_HUB_TOKEN`: Your Docker Hub access token (create in Docker Hub → Account Settings → Security → Access Tokens)

## Method 4: Using docker-compose Push (Simpler)

Add to `docker-compose.yml`:
```yaml
services:
  app:
    build:
      context: .
      dockerfile: docker/app/Dockerfile
    image: yourusername/statistics-for-strava:latest  # Add this line
```

Then build and push:
```bash
docker-compose build app
docker-compose push app
```

## Versioning Strategy

### Semantic Versioning
```bash
# Latest stable release
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:latest .

# Specific version
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:1.0.0 .

# Major version (1.x.x)
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:1 .

# Push all tags
docker push yourusername/statistics-for-strava:latest
docker push yourusername/statistics-for-strava:1.0.0
docker push yourusername/statistics-for-strava:1
```

### Git Tag-Based Versioning
```bash
# Create a git tag
git tag v1.0.0
git push origin v1.0.0

# Build from tag
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:$(git describe --tags) .
docker push yourusername/statistics-for-strava:$(git describe --tags)
```

## Quick Commands Reference

```bash
# 1. Login
docker login

# 2. Build
docker build -f docker/app/Dockerfile -t yourusername/statistics-for-strava:latest .

# 3. Test locally (optional)
docker run -p 8080:8080 yourusername/statistics-for-strava:latest

# 4. Push
docker push yourusername/statistics-for-strava:latest

# 5. Pull and run elsewhere
docker pull yourusername/statistics-for-strava:latest
docker run -p 8080:8080 yourusername/statistics-for-strava:latest
```

## Multi-Arch Build (Optional)

Build for multiple architectures (amd64, arm64):
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t yourusername/statistics-for-strava:latest --push .
```

## Troubleshooting

### Permission Denied
- Ensure you're logged in: `docker login`
- Check token permissions in Docker Hub

### Image Too Large
- Use `.dockerignore` file
- Multi-stage builds (already implemented in your Dockerfile)

### Build Fails
- Check Dockerfile syntax
- Ensure all dependencies are in context
- Review build logs

## Your Repository Setup

Since your project is `robiningelbrecht/statistics-for-strava`, your Docker Hub commands would be:

```bash
docker build -f docker/app/Dockerfile -t robiningelbrecht/statistics-for-strava:latest .
docker push robiningelbrecht/statistics-for-strava:latest
```

## Best Practices

1. **Use Specific Tags**: Don't just use `latest`
2. **Automate with CI/CD**: Use GitHub Actions
3. **Security Scanning**: Enable vulnerability scanning in Docker Hub
4. **Readme**: Add documentation to your Docker Hub repository
5. **Version Consistency**: Match Docker tags with Git tags
