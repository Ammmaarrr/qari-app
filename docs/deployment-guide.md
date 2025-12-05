# Deployment Guide

Complete guide for deploying Qari App to production.

## Overview

Qari App uses a multi-tier architecture:
- **Backend API**: FastAPI on GPU-enabled EC2
- **Database**: RDS PostgreSQL
- **Cache**: ElastiCache Redis  
- **Storage**: S3 for audio files
- **Mobile**: iOS App Store + Google Play Store

---

## Prerequisites

### Required Accounts
- [ ] AWS Account with billing enabled
- [ ] Apple Developer Account ($99/year)
- [ ] Google Play Developer Account ($25 one-time)
- [ ] Domain name (e.g., `qari-app.com`)
- [ ] GitHub repository access

### Required Tools
```bash
# Install locally
brew install terraform  # or: choco install terraform
brew install awscli
npm install -g vercel  # Optional for frontend
```

--

## Part 1: Backend Deployment

### Step 1: Configure AWS Credentials

```bash
aws configure
# AWS Access Key ID: YOUR_KEY
# AWS Secret Access Key: YOUR_SECRET
# Default region: us-east-1
# Default output format: json
```

### Step 2: Prepare Terraform Variables

```bash
cd infra/terraform

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region = "us-east-1"
environment = "production"
db_password = "$(openssl rand -base64 32)"
app_name = "qari-app"
EOF
```

### Step 3: Deploy Infrastructure

```bash
# Initialize
terraform init

# Review plan
terraform plan -out=tfplan

# Apply (creates VPC, RDS, Redis, EC2, S3)
terraform apply tfplan
```

**Outputs to save**:
```bash
terraform output > outputs.txt
# Save: database_endpoint, redis_endpoint, ml_instance_public_ip, s3_bucket_name
```

### Step 4: Configure Backend Application

SSH into EC2 instance:
```bash
ML_IP=$(terraform output -raw ml_instance_public_ip)
ssh -i ~/.ssh/your-key.pem ubuntu@$ML_IP
```

Configure environment:
```bash
cd /home/ubuntu/qari-app/backend

# Edit .env
nano .env
```

Add production values:
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://qariapp:PASSWORD@RDS_ENDPOINT:5432/qariapp
REDIS_URL=redis://REDIS_ENDPOINT:6379
S3_BUCKET=qari-app-audio-production
AWS_REGION=us-east-1
WHISPER_MODEL=large-v2
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn  # Optional
```

### Step 5: Build and Start

```bash
# Build production image
docker build -f Dockerfile.production -t qari-backend:latest .

# Start with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Verify
curl http://localhost:8000/health
```

### Step 6: Configure Domain & SSL

Install nginx and certbot:
```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Configure nginx:
```bash
sudo nano /etc/nginx/sites-available/qari-app
```

Add configuration:
```nginx
server {
    server_name api.qari-app.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site and get SSL:
```bash
sudo ln -s /etc/nginx/sites-available/qari-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d api.qari-app.com
```

### Step 7: Setup Monitoring

Install Prometheus and Grafana:
```bash
# Add metrics endpoint to nginx
sudo nano /etc/nginx/sites-available/qari-app
```

Add:
```nginx
location /metrics {
    proxy_pass http://localhost:8000/metrics;
    allow 10.0.0.0/16;  # VPC only
    deny all;
}
```

---

## Part 2: Database Setup

### Step 1: Run Migrations

```bash
cd /home/ubuntu/qari-app/backend

# Inside container
docker exec -it qari-backend bash

# Run migrations
alembic upgrade head

# Create initial admin user (if needed)
python -m app.scripts.create_admin
```

### Step 2: Configure Backups

Automated backups are enabled via RDS (7-day retention).

For additional backups:
```bash
# Create backup script
cat > /home/ubuntu/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h $DB_HOST -U qariapp qariapp | gzip > /tmp/backup_$DATE.sql.gz
aws s3 cp /tmp/backup_$DATE.sql.gz s3://qari-app-backups/
rm /tmp/backup_$DATE.sql.gz
EOF

chmod +x /home/ubuntu/backup-db.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /home/ubuntu/backup-db.sh" | crontab -
```

---

## Part 3: Mobile App Deployment

### iOS Deployment

#### Step 1: Prepare Xcode Project

```bash
cd mobile

# Update API endpoint
nano src/services/api.ts
```

Change to production:
```typescript
const API_BASE_URL = 'https://api.qari-app.com';
```

#### Step 2: Build for Release

```bash
# Open in Xcode
open ios/QariApp.xcworkspace

# In Xcode:
# 1. Select "Any iOS Device (arm64)"
# 2. Product > Archive
# 3. Wait for build to complete
```

#### Step 3: Submit to App Store

```
1. In Organizer > Distribute App
2. Choose "App Store Connect"
3. Upload
4. Log into App Store Connect
5. Fill app metadata
6. Submit for review
```

### Android Deployment

#### Step 1: Generate Signing Key

```bash
cd mobile/android/app

keytool -genkeypair -v -storetype PKCS12 \
  -keystore qari-app-release.keystore \
  -alias qari-app \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

#### Step 2: Configure Gradle

Edit `android/gradle.properties`:
```properties
QARI_UPLOAD_STORE_FILE=qari-app-release.keystore
QARI_UPLOAD_KEY_ALIAS=qari-app
QARI_UPLOAD_STORE_PASSWORD=your_password
QARI_UPLOAD_KEY_PASSWORD=your_password
```

#### Step 3: Build Release APK

```bash
cd android
./gradlew bundleRelease

# Output: app/build/outputs/bundle/release/app-release.aab
```

#### Step 4: Upload to Play Store

```
1. Go to Google Play Console
2. Create new release
3. Upload app-release.aab
4. Fill store listing
5. Submit for review
```

---

## Part 4: Monitoring & Alerts

### CloudWatch Alarms

```bash
# Create alarm for high CPU
aws cloudwatch put-metric-alarm \
  --alarm-name qari-app-high-cpu \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Error Tracking

```bash
# Install Sentry (optional)
pip install sentry-sdk[fastapi]
```

Add to `app/main.py`:
```python
import sentry_sdk
sentry_sdk.init(
    dsn="your_sentry_dsn",
    environment="production",
    traces_sample_rate=0.1
)
```

---

## Part 5: Post-Deployment

### Smoke Tests

```bash
# Health check
curl https://api.qari-app.com/health

# Test analyze endpoint
curl -X POST https://api.qari-app.com/api/v1/recordings/analyze \
  -F "user_id=test-$(date +%s)" \
  -F "surah=1" \
  -F "ayah=1" \
  -F "audio_file=@test.wav"
```

### Load Testing

```bash
# Install k6
brew install k6

# Run load test
k6 run load-test.js --vus 10 --duration 30s
```

### Update DNS

Point domain to EC2 instance:
```
A record: api.qari-app.com -> EC2_PUBLIC_IP
```

---

## Rollback Procedure

If deployment fails:

```bash
# Backend rollback
cd /home/ubuntu/qari-app/backend
git checkout previous-commit
docker-compose down
docker-compose up -d --build

# Database rollback
alembic downgrade -1

# Mobile rollback
# Submit new build to stores with previous version
```

---

## Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Environment variables configured
- [ ] SSL certificates ready
- [ ] Database migrations tested
- [ ] Backup strategy in place

### Deployment
- [ ] Infrastructure deployed (Terraform applied)
- [ ] Backend running and healthy
- [ ] Database migrations applied
- [ ] SSL/TLS configured
- [ ] Domain pointing to server
- [ ] Mobile apps built

### Post-Deployment
- [ ] Smoke tests passing
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Backups automated
- [ ] Documentation updated

---

## Support & Troubleshooting

Common issues:

**Backend not starting**: Check logs with `docker-compose logs`  
**SSL errors**: Verify certbot renewal with `sudo certbot renew --dry-run`  
**Database connection issues**: Check security groups allow port 5432  
**High latency**: Monitor GPU usage, may need to scale

---

**Your Qari App is now deployed to production!** 🎉
