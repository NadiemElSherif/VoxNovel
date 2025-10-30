#!/bin/bash

# VoxNovel Proxmox Deployment Script
# This script automates the deployment of VoxNovel on Proxmox with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_status "Starting VoxNovel deployment for Proxmox..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    print_status "Docker installed successfully"
else
    print_status "Docker is already installed"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose is already installed"
fi

# Check if NVIDIA Container Toolkit is installed (optional)
if command -v nvidia-smi &> /dev/null && ! command -v nvidia-container-cli &> /dev/null; then
    print_warning "NVIDIA GPU detected but NVIDIA Container Toolkit not found"
    read -p "Do you want to install NVIDIA Container Toolkit for GPU support? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing NVIDIA Container Toolkit..."
        distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
        curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
        curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
        apt update
        apt install -y nvidia-container-toolkit
        systemctl restart docker
        print_status "NVIDIA Container Toolkit installed successfully"
    fi
fi

# Check if in correct directory
if [ ! -f "docker-compose.proxmox.yml" ]; then
    print_error "docker-compose.proxmox.yml not found. Please run this script from the VoxNovel directory."
    exit 1
fi

# Create necessary directories
print_status "Creating data directories..."
mkdir -p data/{uploads,output_audiobooks,Working_files,Final_combined_output_audio,tortoise}
mkdir -p nginx

# Set permissions
print_status "Setting permissions..."
chmod -R 755 data/
chmod +x web_server.py

# Stop existing containers if running
if docker-compose -f docker-compose.proxmox.yml ps -q | grep -q .; then
    print_status "Stopping existing containers..."
    docker-compose -f docker-compose.proxmox.yml down
fi

# Build and start containers
print_status "Building Docker images..."
docker-compose -f docker-compose.proxmox.yml build

print_status "Starting containers..."
docker-compose -f docker-compose.proxmox.yml up -d

# Wait for containers to be ready
print_status "Waiting for VoxNovel to initialize..."
sleep 30

# Check if containers are running
if docker-compose -f docker-compose.proxmox.yml ps | grep -q "Up"; then
    print_status "VoxNovel is now running!"

    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    echo ""
    echo "============================================"
    echo "🎭 VoxNovel Deployment Complete!"
    echo "============================================"
    echo "Web Interface: http://${SERVER_IP}:8080"
    echo ""
    echo "Useful Commands:"
    echo "  View logs: docker-compose -f docker-compose.proxmox.yml logs -f"
    echo "  Stop service: docker-compose -f docker-compose.proxmox.yml down"
    echo "  Restart service: docker-compose -f docker-compose.proxmox.yml restart"
    echo ""
    echo "Data is stored in: $(pwd)/data/"
    echo "============================================"
else
    print_error "Failed to start VoxNovel containers"
    print_error "Check logs with: docker-compose -f docker-compose.proxmox.yml logs"
    exit 1
fi

# Optional: Test GPU support
if command -v nvidia-smi &> /dev/null; then
    print_status "Testing GPU support..."
    if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
        print_status "GPU support is working!"
    else
        print_warning "GPU support is not working properly. Container will use CPU for processing."
    fi
fi

print_status "Deployment completed successfully!"