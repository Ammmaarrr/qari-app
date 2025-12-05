#!/bin/bash

# User data script for EC2 ML inference instance
# This script runs on first boot to configure the instance

set -e

echo "=== Qari App ML Inference Instance Setup ==="

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install NVIDIA Docker runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update
apt-get install -y nvidia-docker2
systemctl restart docker

# Clone application repository
cd /home/ubuntu
git clone https://github.com/your-org/qari-app.git
cd qari-app/backend

# Set environment variables
cat > .env << EOF
ENVIRONMENT=${environment}
DATABASE_URL=$DATABASE_URL
REDIS_URL=$REDIS_URL
S3_BUCKET=$S3_BUCKET
AWS_REGION=$AWS_REGION
WHISPER_MODEL=large-v2
EOF

# Build and start backend
docker-compose up -d --build

# Set up log rotation
cat > /etc/logrotate.d/qari-app << EOF
/var/log/qari-app/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 ubuntu ubuntu
}
EOF

# Set up health check monitoring
cat > /home/ubuntu/health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8000/health; then
    echo "Health check failed, restarting container..."
    cd /home/ubuntu/qari-app/backend
    docker-compose restart
fi
EOF

chmod +x /home/ubuntu/health-check.sh

# Add health check to cron (every 5 minutes)
echo "*/5 * * * * /home/ubuntu/health-check.sh >> /var/log/health-check.log 2>&1" | crontab -

echo "=== Setup complete ==="
