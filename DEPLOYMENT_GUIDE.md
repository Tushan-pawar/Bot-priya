# 🚀 Deployment Guide - Production Setup

Complete guide for deploying Priya in production environments with high availability, monitoring, and scalability.

## 🎯 Deployment Options

### 1. Cloud VPS (Recommended)
**Best for:** Most users, good balance of cost and performance
- **Providers:** DigitalOcean, Linode, Vultr, AWS EC2
- **Cost:** $5-20/month
- **Setup time:** 30 minutes

### 2. Dedicated Server
**Best for:** High-traffic servers, maximum performance
- **Providers:** Hetzner, OVH, Contabo
- **Cost:** $30-100/month
- **Setup time:** 1 hour

### 3. Docker Container
**Best for:** Easy deployment, scaling, development
- **Platforms:** Any Docker-compatible host
- **Cost:** Variable
- **Setup time:** 15 minutes

### 4. Serverless (Advanced)
**Best for:** Auto-scaling, pay-per-use
- **Platforms:** AWS Lambda, Google Cloud Functions
- **Cost:** Pay per request
- **Setup time:** 2-3 hours

## 🖥️ VPS Deployment (Step-by-Step)

### Step 1: Choose VPS Provider

**Recommended Specs:**
- **CPU:** 2+ cores
- **RAM:** 4GB+ (8GB recommended)
- **Storage:** 20GB+ SSD
- **OS:** Ubuntu 22.04 LTS

**Provider Comparison:**
| Provider | 4GB RAM | 8GB RAM | Pros |
|----------|---------|---------|------|
| DigitalOcean | $24/mo | $48/mo | Easy, good docs |
| Linode | $24/mo | $48/mo | Reliable, fast |
| Vultr | $12/mo | $24/mo | Cheap, global |
| AWS EC2 | $20/mo | $40/mo | Scalable, enterprise |

### Step 2: Server Setup

**Connect to server:**
```bash
ssh root@your_server_ip
```

**Update system:**
```bash
apt update && apt upgrade -y
```

**Install Python and dependencies:**
```bash
# Install Python 3.11
apt install python3.11 python3.11-pip python3.11-venv -y

# Install system dependencies
apt install git ffmpeg sqlite3 curl -y

# Install Ollama (optional, for local AI)
curl -fsSL https://ollama.ai/install.sh | sh
```

**Create user for bot:**
```bash
adduser priya
usermod -aG sudo priya
su - priya
```

### Step 3: Deploy Bot

**Clone repository:**
```bash
git clone https://github.com/your-repo/Bot-priya.git
cd Bot-priya
```

**Setup Python environment:**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Configure environment:**
```bash
cp .env.example .env
nano .env
```

**Add your configuration:**
```env
# Required
DISCORD_TOKEN=your_discord_token

# AI Providers (add 3-5 for reliability)
GROQ_API_KEY=your_groq_key
TOGETHER_API_KEY=your_together_key
HUGGINGFACE_API_KEY=your_hf_key
ANTHROPIC_API_KEY=your_anthropic_key

# Production settings
LOG_LEVEL=INFO
LOG_FILE=/home/priya/Bot-priya/logs/priya.log
MAX_MEMORY_MB=1000
MAX_CONCURRENT_REQUESTS=20

# Database
DATABASE_PATH=/home/priya/Bot-priya/data/priya.db
BACKUP_ENABLED=true
BACKUP_INTERVAL=3600
```

**Test bot:**
```bash
python main.py
```

### Step 4: Production Setup

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/priya-bot.service
```

**Service configuration:**
```ini
[Unit]
Description=Priya Discord Bot
After=network.target

[Service]
Type=simple
User=priya
WorkingDirectory=/home/priya/Bot-priya
Environment=PATH=/home/priya/Bot-priya/venv/bin
ExecStart=/home/priya/Bot-priya/venv/bin/python main.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=priya-bot

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/home/priya/Bot-priya

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable priya-bot
sudo systemctl start priya-bot
```

**Check status:**
```bash
sudo systemctl status priya-bot
sudo journalctl -u priya-bot -f
```

## 🐳 Docker Deployment

### Step 1: Create Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama (optional)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data logs

# Run as non-root user
RUN useradd -m -u 1000 priya && chown -R priya:priya /app
USER priya

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Start bot
CMD ["python", "main.py"]
```

### Step 2: Create docker-compose.yml
```yaml
version: '3.8'

services:
  priya-bot:
    build: .
    container_name: priya-bot
    restart: unless-stopped
    
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - TOGETHER_API_KEY=${TOGETHER_API_KEY}
      - HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY}
      - LOG_LEVEL=INFO
      - DATABASE_PATH=/app/data/priya.db
    
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    
    ports:
      - "8080:8080"  # Web dashboard
    
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Database backup service
  backup:
    image: alpine:latest
    container_name: priya-backup
    restart: unless-stopped
    
    volumes:
      - ./data:/data
      - ./backups:/backups
    
    command: >
      sh -c "
        while true; do
          sleep 3600
          tar -czf /backups/backup-$(date +%Y%m%d-%H%M%S).tar.gz /data
          find /backups -name '*.tar.gz' -mtime +7 -delete
        done
      "

  # Optional: Monitoring
  monitoring:
    image: prom/prometheus:latest
    container_name: priya-monitoring
    restart: unless-stopped
    
    ports:
      - "9090:9090"
    
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
```

### Step 3: Deploy with Docker
```bash
# Create environment file
cp .env.example .env
# Edit .env with your tokens

# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f priya-bot

# Update bot
docker-compose pull
docker-compose up -d --build
```

## ☁️ Cloud Platform Deployment

### AWS EC2 Deployment

**Launch EC2 Instance:**
1. Choose Ubuntu 22.04 LTS AMI
2. Instance type: t3.medium (2 vCPU, 4GB RAM)
3. Configure security group:
   - SSH (22) from your IP
   - HTTP (80) for dashboard
   - HTTPS (443) for dashboard
4. Create and download key pair

**Connect and setup:**
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Follow VPS deployment steps above
```

**Setup domain (optional):**
```bash
# Install nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/priya-bot
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/priya-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Google Cloud Platform

**Create VM Instance:**
```bash
# Using gcloud CLI
gcloud compute instances create priya-bot \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-medium \
    --zone=us-central1-a \
    --tags=http-server,https-server
```

**Setup firewall:**
```bash
gcloud compute firewall-rules create allow-priya-dashboard \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server
```

### DigitalOcean App Platform

**Create app.yaml:**
```yaml
name: priya-bot
services:
- name: bot
  source_dir: /
  github:
    repo: your-username/Bot-priya
    branch: main
  run_command: python main.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  
  envs:
  - key: DISCORD_TOKEN
    value: your_token
    type: SECRET
  - key: GROQ_API_KEY
    value: your_key
    type: SECRET
```

## 📊 Monitoring & Logging

### Log Management

**Setup log rotation:**
```bash
sudo nano /etc/logrotate.d/priya-bot
```

**Logrotate configuration:**
```
/home/priya/Bot-priya/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 priya priya
    postrotate
        systemctl reload priya-bot
    endscript
}
```

### Health Monitoring

**Create health check script:**
```bash
nano /home/priya/health-check.sh
```

**Health check script:**
```bash
#!/bin/bash

# Check if bot process is running
if ! pgrep -f "python main.py" > /dev/null; then
    echo "Bot process not running, restarting..."
    systemctl restart priya-bot
    exit 1
fi

# Check bot responsiveness
if ! curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "Bot not responding, restarting..."
    systemctl restart priya-bot
    exit 1
fi

echo "Bot is healthy"
```

**Setup cron job:**
```bash
chmod +x /home/priya/health-check.sh
crontab -e

# Add line:
*/5 * * * * /home/priya/health-check.sh >> /home/priya/health-check.log 2>&1
```

### Performance Monitoring

**Install monitoring tools:**
```bash
# Install htop for system monitoring
sudo apt install htop -y

# Install netdata for web-based monitoring
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

**Access monitoring:**
- System stats: `htop`
- Web dashboard: `http://your-server:19999`
- Bot dashboard: `http://your-server:8080`

## 🔒 Security Hardening

### Firewall Setup
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow bot dashboard
sudo ufw allow 8080

# Allow monitoring (optional)
sudo ufw allow 19999

# Check status
sudo ufw status
```

### SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Secure Configuration
```bash
# Secure .env file
chmod 600 .env

# Secure data directory
chmod 700 data/

# Regular security updates
sudo apt update && sudo apt upgrade -y
```

## 📈 Scaling & Performance

### Vertical Scaling (Upgrade Server)
```bash
# Monitor resource usage
htop
df -h
free -h

# Upgrade when needed:
# - CPU usage > 80%
# - RAM usage > 90%
# - Disk usage > 85%
```

### Horizontal Scaling (Multiple Instances)
```yaml
# docker-compose.yml for load balancing
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - bot1
      - bot2

  bot1:
    build: .
    environment:
      - INSTANCE_ID=1
    
  bot2:
    build: .
    environment:
      - INSTANCE_ID=2
```

### Database Optimization
```bash
# Regular database maintenance
sqlite3 data/priya.db "VACUUM;"
sqlite3 data/priya.db "ANALYZE;"

# Monitor database size
du -h data/priya.db
```

## 🔄 Backup & Recovery

### Automated Backups
```bash
# Create backup script
nano /home/priya/backup.sh
```

**Backup script:**
```bash
#!/bin/bash

BACKUP_DIR="/home/priya/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp data/priya.db $BACKUP_DIR/priya_db_$DATE.db

# Backup configuration
cp .env $BACKUP_DIR/env_$DATE.backup

# Backup logs (last 7 days)
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Upload to cloud (optional)
# aws s3 cp $BACKUP_DIR/ s3://your-bucket/priya-backups/ --recursive

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Schedule backups:**
```bash
chmod +x /home/priya/backup.sh
crontab -e

# Daily backup at 2 AM
0 2 * * * /home/priya/backup.sh >> /home/priya/backup.log 2>&1
```

### Disaster Recovery
```bash
# Stop bot
sudo systemctl stop priya-bot

# Restore database
cp backups/priya_db_YYYYMMDD_HHMMSS.db data/priya.db

# Restore configuration
cp backups/env_YYYYMMDD_HHMMSS.backup .env

# Start bot
sudo systemctl start priya-bot
```

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Server meets minimum requirements
- [ ] All API keys obtained and tested
- [ ] Domain name configured (if using)
- [ ] SSL certificate ready (if using HTTPS)
- [ ] Backup strategy planned

### Deployment
- [ ] Bot code deployed and tested
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Systemd service created and enabled
- [ ] Firewall configured
- [ ] Monitoring setup

### Post-Deployment
- [ ] Bot responds to commands
- [ ] Voice features working (if enabled)
- [ ] Memory system functioning
- [ ] Logs being generated
- [ ] Backups running
- [ ] Health checks passing
- [ ] Performance monitoring active

### Maintenance
- [ ] Regular security updates
- [ ] Log rotation configured
- [ ] Backup verification
- [ ] Performance monitoring
- [ ] Capacity planning

---

**Your Priya bot is now production-ready!** 🎉

For ongoing support and updates, check the other guides in this repository and join our community Discord server.