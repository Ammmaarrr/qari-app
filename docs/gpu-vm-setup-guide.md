# GPU VM Setup Guide

Complete guide for setting up the ML inference server on a GPU-enabled instance.

## Prerequisites

- AWS Account with EC2 access
- Terraform installed locally
- SSH key pair created in AWS

## 1. Deploy Infrastructure

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Set variables
export TF_VAR_db_password="your-secure-password-here"

# Deploy
terraform plan -out=tfplan
terraform apply tfplan

# Note the outputs
# - ml_instance_public_ip
# - database_endpoint
# - redis_endpoint
# - s3_bucket_name
```

## 2. SSH into GPU Instance

```bash
# Get instance IP from Terraform output
ML_INSTANCE_IP=$(terraform output -raw ml_instance_public_ip)

# SSH (using your key pair)
ssh -i ~/.ssh/your-key.pem ubuntu@$ML_INSTANCE_IP
```

## 3. Verify GPU Availability

```bash
# Check NVIDIA driver
nvidia-smi

# Expected output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 525.x.xx    Driver Version: 525.x.xx    CUDA Version: 12.0     |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  Tesla T4            Off  | 00000000:00:1E.0 Off |                    0 |
# | N/A   32C    P8     9W /  70W |      0MiB / 15109MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

## 4. Verify Docker & NVIDIA Runtime

```bash
# Check Docker version
docker --version

# Test NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Should show GPU info from within container
```

## 5. Configure Environment

```bash
cd /home/ubuntu/qari-app/backend

# Edit .env file
sudo nano .env
```

Add/update these values:

```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://qariapp:PASSWORD@RDS_ENDPOINT:5432/qariapp
REDIS_URL=redis://REDIS_ENDPOINT:6379
S3_BUCKET=qari-app-audio-production
AWS_REGION=us-east-1
WHISPER_MODEL=large-v2
LOG_LEVEL=INFO
```

Replace:
- `PASSWORD` - from Terraform variable
- `RDS_ENDPOINT` - from Terraform output
- `REDIS_ENDPOINT` - from Terraform output

## 6. Pull and Build Container

```bash
cd /home/ubuntu/qari-app/backend

# Pull latest code
git pull origin main

# Build with GPU support
docker-compose -f docker-compose.production.yml build

# Or use production Dockerfile
docker build -f Dockerfile.production -t qari-backend:latest .
```

## 7. Start Services

```bash
# Start in detached mode
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose logs -f

# Verify health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "qari-app-api"
}
```

## 8. Test Whisper GPU Inference

```bash
# Enter container
docker exec -it qari-backend bash

# Test Whisper with GPU
python -c "
import whisper
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU count: {torch.cuda.device_count()}')
model = whisper.load_model('base', device='cuda')
print('Whisper model loaded successfully on GPU!')
"
```

Expected output:
```
CUDA available: True
GPU count: 1
Whisper model loaded successfully on GPU!
```

## 9. Performance Tuning

### GPU Memory Optimization

Edit `app/services/asr_service.py`:

```python
# Use FP16 for faster inference
import whisper
model = whisper.load_model("large-v2", device="cuda", download_root="/models")
model = model.half()  # Convert to FP16
```

### Batch Processing

For multiple requests, batch them:

```python
# In asr_service.py
def transcribe_batch(audio_paths):
    results = []
    for audio_path in audio_paths:
        result = model.transcribe(audio_path, fp16=True)
        results.append(result)
    return results
```

### Worker Configuration

Edit `docker-compose.production.yml`:

```yaml
services:
  backend:
    command: >
      gunicorn app.main:app
      --workers 2
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8000
      --timeout 300
      --graceful-timeout 30
```

**Note**: Limit workers to 2-4 with GPU to avoid memory issues.

## 10. Monitoring GPU Usage

### Install nvidia-smi monitoring

```bash
# Create monitoring script
cat > /home/ubuntu/monitor-gpu.sh << 'EOF'
#!/bin/bash
while true; do
    nvidia-smi --query-gpu=timestamp,utilization.gpu,utilization.memory,memory.used,memory.total \
                --format=csv,noheader,nounits >> /var/log/gpu-metrics.log
    sleep 10
done
EOF

chmod +x /home/ubuntu/monitor-gpu.sh

# Run in background
nohup /home/ubuntu/monitor-gpu.sh &
```

### View GPU metrics

```bash
tail -f /var/log/gpu-metrics.log
```

## 11. Load Balancer Setup (Optional)

For production, add Application Load Balancer:

```bash
# In terraform/main.tf, add:
resource "aws_lb" "main" {
  name               = "qari-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "backend" {
  name     = "qari-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    path = "/health"
  }
}
```

## 12. SSL/TLS Setup

```bash
# Install certbot
sudo snap install --classic certbot

# Get certificate
sudo certbot certonly --standalone -d api.your-domain.com

# Configure nginx reverse proxy
sudo apt-get install nginx

# Edit /etc/nginx/sites-available/qari-app
server {
    listen 443 ssl;
    server_name api.your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 13. Backup & Recovery

### Database Backups

Automated via RDS (7-day retention configured in Terraform).

Manual backup:
```bash
pg_dump -h $RDS_ENDPOINT -U qariapp qariapp > backup.sql
aws s3 cp backup.sql s3://qari-app-backups/$(date +%Y%m%d).sql
```

### Model Checkpoint Backups

```bash
# Sync models to S3
aws s3 sync /app/models/checkpoints s3://qari-app-models/checkpoints/
```

## 14. Troubleshooting

### GPU not detected in container

```bash
# Check NVIDIA Docker runtime
cat /etc/docker/daemon.json

# Should contain:
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime"
    }
  }
}

# Restart Docker
sudo systemctl restart docker
```

### Out of GPU memory

```bash
# Check GPU memory
nvidia-smi

# Reduce batch size or use smaller model
# Edit app/config.py
WHISPER_MODEL = "base"  # instead of "large-v2"
```

### High latency

```bash
# Enable request queuing
# Add Redis queue for async processing
# See backend/app/services/queue.py
```

## 15. Cost Optimization

- **Use Spot Instances** for non-critical workloads (60-70% savings)
- **Auto-stop** instances during low traffic (nights/weekends)
- **Use smaller models** (base/small) when accuracy allows
- **Cache frequent requests** in Redis

```bash
# Auto-stop script (add to cron)
0 22 * * * aws ec2 stop-instances --instance-ids i-xxxxx  # Stop at 10 PM
0 6 * * 1-5 aws ec2 start-instances --instance-ids i-xxxxx  # Start at 6 AM weekdays
```

## Summary Checklist

- [ ] Infrastructure deployed via Terraform
- [ ] SSH access verified
- [ ] GPU detected (nvidia-smi working)
- [ ] Docker & NVIDIA runtime configured
- [ ] Environment variables set
- [ ] Application containers running
- [ ] Health check passing
- [ ] Whisper GPU inference tested
- [ ] Monitoring configured
- [ ] Backups automated
- [ ] SSL/TLS configured (if using custom domain)

Your GPU-enabled ML inference server is now ready for production!
