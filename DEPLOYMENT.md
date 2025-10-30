# VoxNovel Proxmox Deployment Guide

This guide explains how to deploy VoxNovel on a Proxmox server using Docker containers with a simple web interface.

## Prerequisites

### Hardware Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB+ recommended
- **GPU**: NVIDIA GPU with 4GB+ VRAM (optional but recommended for faster processing)
- **Storage**: 50GB+ available space

### Software Requirements
- Proxmox VE 7.0+
- LXC container with Debian 11+ or Ubuntu 20.04+
- Docker and Docker Compose installed
- GPU passthrough configured (if using GPU acceleration)

## Installation

### 1. Prepare the LXC Container

Create a privileged LXC container with the following specifications:
- **OS**: Debian 11 (Bullseye) or Ubuntu 20.04+
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+
- **GPU Passthrough**: Enabled (if using NVIDIA GPU)

### 2. Install Docker and Docker Compose

```bash
# Update system packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add user to docker group (optional)
usermod -aG docker $USER
```

### 3. Install NVIDIA Container Toolkit (GPU Support Only)

```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
apt update
apt install -y nvidia-container-toolkit

# Restart Docker
systemctl restart docker
```

### 4. Deploy VoxNovel

Clone the repository and deploy:

```bash
# Clone VoxNovel (or copy files from your local setup)
git clone https://github.com/DrewThomasson/VoxNovel.git
cd VoxNovel

# Create data directories
mkdir -p data/{uploads,output_audiobooks,Working_files,Final_combined_output_audio,tortoise}
mkdir -p nginx

# Set permissions
chmod -R 755 data/
chmod +x web_server.py

# Build and start containers
docker-compose -f docker-compose.proxmox.yml up -d
```

### 5. Configure Nginx (Optional)

Create `nginx/nginx.conf` for reverse proxy:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream voxnovel {
        server voxnovel:8080;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://voxnovel;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Increase client upload size for large ebook files
        client_max_body_size 100M;
    }

    # Uncomment for HTTPS support
    # server {
    #     listen 443 ssl;
    #     server_name your-domain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/cert.pem;
    #     ssl_certificate_key /etc/nginx/ssl/key.pem;
    #
    #     location / {
    #         proxy_pass http://voxnovel;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    #
    #     client_max_body_size 100M;
    # }
}
```

## Usage

### Accessing the Web Interface

Once deployed, access the VoxNovel web interface at:
- **Direct**: `http://your-server-ip:8080`
- **With Nginx**: `http://your-domain.com`

The web interface provides:
- **File Upload**: Drag-and-drop or click to upload ebook files
- **Processing Options**: Select TTS model, GPU acceleration, chapter delimiters
- **Real-time Status**: Monitor processing progress with live updates
- **Download Management**: Access completed audiobooks and job history
- **Mobile Friendly**: Works on tablets and mobile devices

### Alternative Launch Methods

If you prefer to launch the web interface directly:

```bash
# Method 1: Use the web launcher (recommended)
python start_web_gui.py

# Method 2: Use the web GUI script directly
python gui_run_web.py

# Method 3: Force web mode with environment variable
VOXNOVEL_WEB_MODE=1 python gui_run.py
```

The original `gui_run.py` now automatically detects headless environments (like Docker) and launches the web interface automatically.

### Processing Books

1. **Upload**: Drag and drop or select an ebook file
2. **Configure**: Choose TTS model and processing options
3. **Process**: Click "Process Book" to start generation
4. **Download**: Access completed audiobooks from the status page or jobs list

### Supported File Formats
- EPUB, PDF, MOBI, TXT, HTML, RTF, FB2, ODT, CBR, CBZ
- Best results with EPUB or MOBI for automatic chapter detection

## Configuration

### Environment Variables

Modify `docker-compose.proxmox.yml` to adjust:

```yaml
environment:
  - NVIDIA_VISIBLE_DEVICES=all  # GPU visibility
  - CUDA_VISIBLE_DEVICES=0      # Specific GPU device
```

### Volume Configuration

Persistent data is stored in:
- `./data/uploads/` - Uploaded ebook files
- `./data/output_audiobooks/` - Generated audiobooks
- `./data/Working_files/` - Temporary processing files
- `./data/tortoise/` - Voice samples

### Performance Tuning

#### GPU vs CPU Processing
- **GPU**: 10x faster audio generation (recommended)
- **CPU**: Slower but more reliable for complex models

#### Memory Usage
- **XTTS Model**: 2-4GB VRAM
- **Tortoise Model**: 6-8GB VRAM
- **BookNLP Processing**: 2-4GB RAM

## Monitoring and Maintenance

### Check Container Status

```bash
# View running containers
docker-compose -f docker-compose.proxmox.yml ps

# View logs
docker-compose -f docker-compose.proxmox.yml logs -f voxnovel

# Access container shell
docker-compose -f docker-compose.proxmox.yml exec voxnovel bash
```

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# Check GPU usage (NVIDIA)
nvidia-smi
```

### Backup Data

```bash
# Backup important data
tar -czf voxnovel-backup-$(date +%Y%m%d).tar.gz data/

# Restore from backup
tar -xzf voxnovel-backup-YYYYMMDD.tar.gz
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs for errors
docker-compose -f docker-compose.proxmox.yml logs voxnovel

# Rebuild container
docker-compose -f docker-compose.proxmox.yml down
docker-compose -f docker-compose.proxmox.yml build --no-cache
docker-compose -f docker-compose.proxmox.yml up -d
```

#### 2. GPU Not Detected
```bash
# Check GPU visibility in container
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Verify NVIDIA container toolkit
nvidia-container-cli info
```

#### 3. Out of Memory Errors
- Reduce batch sizes in TTS processing
- Use smaller models (XTTS instead of Tortoise)
- Increase system RAM or swap space

#### 4. Slow Processing
- Ensure GPU acceleration is working
- Check if container has sufficient resources allocated
- Monitor CPU and GPU utilization

#### 5. File Upload Issues
- Check file size limits (default 100MB)
- Verify permissions on upload directory
- Ensure sufficient disk space

### Performance Optimization

1. **Use GPU Acceleration**: Enable NVIDIA GPU for 10x speed improvement
2. **Optimize Memory**: Allocate sufficient RAM to avoid swapping
3. **Storage**: Use fast SSD for working files
4. **Network**: Ensure adequate bandwidth for file uploads

## Security Considerations

1. **Network Access**: Consider using VPN or SSH tunneling
2. **Authentication**: Add authentication to the web interface if needed
3. **File Uploads**: Validate file types and scan for malware
4. **Resource Limits**: Set appropriate resource limits in Docker
5. **Updates**: Regularly update Docker images and dependencies

## Scaling and Load Balancing

For multiple users, consider:

1. **Multiple Containers**: Run multiple VoxNovel instances
2. **Load Balancer**: Use HAProxy or Nginx for load balancing
3. **Queue System**: Implement job queue for concurrent processing
4. **Distributed Storage**: Use shared storage for multiple nodes

## Support

- **GitHub Issues**: Report bugs at https://github.com/DrewThomasson/VoxNovel/issues
- **Documentation**: Check main VoxNovel documentation
- **Community**: Join discussions in GitHub discussions