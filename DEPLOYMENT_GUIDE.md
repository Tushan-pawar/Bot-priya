# 🚀 Complete Integration & Deployment Guide

## 📋 Table of Contents
1. [Discord Bot Setup](#discord-bot-setup)
2. [Installation Methods](#installation-methods)
3. [Configuration Modes](#configuration-modes)
4. [Running the Bot](#running-the-bot)
5. [Usage Guide](#usage-guide)
6. [Troubleshooting](#troubleshooting)

---

## 🤖 Discord Bot Setup

### Step 1: Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Name it **"Priya"** and click **"Create"**

### Step 2: Create Bot User
1. Go to **"Bot"** section
2. Click **"Add Bot"**
3. Copy the **Token** (keep it secret!)
4. Enable these **Privileged Gateway Intents**:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent

### Step 3: Set Bot Permissions
1. Go to **"OAuth2" → "URL Generator"**
2. Select **Scopes**: `bot`
3. Select **Bot Permissions**:
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Connect (Voice)
   - ✅ Speak (Voice)
   - ✅ Use Voice Activity
   - ✅ Read Message History
   - ✅ Add Reactions

### Step 4: Invite Bot to Server
1. Copy the generated URL
2. Open in browser and select your server
3. Click **"Authorize"**

---

## 💻 Installation Methods

### Method 1: Quick Start (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/your-repo/Bot-priya.git
cd Bot-priya

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Edit .env with your Discord token

# 4. Run bot
python main.py
```

### Method 2: Virtual Environment (Safer)
```bash
# 1. Create virtual environment
python -m venv priya-env

# 2. Activate environment
# Windows:
priya-env\Scripts\activate
# macOS/Linux:
source priya-env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run bot
python main.py
```

### Method 3: Docker (Advanced)
```dockerfile
# Create Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
# Build and run
docker build -t priya-bot .
docker run -d --env-file .env priya-bot
```

---

## ⚙️ Configuration Modes

### 🌐 Cloud-Only Mode (Easiest)
**Best for**: Beginners, low-end hardware, instant setup

```env
# .env file
DISCORD_TOKEN=your_discord_token

# Add at least one API key
GROQ_API_KEY=your_groq_key
TOGETHER_API_KEY=your_together_key
HUGGINGFACE_API_KEY=your_hf_key
```

**Pros**: ✅ Works anywhere, ✅ Fast responses, ✅ No local storage
**Cons**: ❌ Needs internet, ❌ API rate limits

### 🔄 Hybrid Mode (Recommended)
**Best for**: Most users, balanced performance

```bash
# 1. Install Ollama
# Windows/macOS: Download from ollama.ai
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull models
ollama pull llama3.2    # 2GB - Fast, good quality
ollama pull mistral     # 4GB - Better quality

# 3. Setup .env
DISCORD_TOKEN=your_discord_token
GROQ_API_KEY=your_groq_key  # Backup
```

**Pros**: ✅ Best of both worlds, ✅ Privacy + reliability
**Cons**: ❌ Needs 8GB+ RAM

### 🏠 Full Local Mode (Privacy)
**Best for**: Privacy-focused, powerful hardware

```bash
# 1. Install all local models
ollama pull llama3.2
ollama pull llama3.1
ollama pull mistral
ollama pull codellama

# 2. Install voice models
pip install faster-whisper TTS

# 3. Install FFmpeg
# Windows: Download from ffmpeg.org
# macOS: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# 4. Setup .env (minimal)
DISCORD_TOKEN=your_discord_token
LOG_LEVEL=INFO
```

**Pros**: ✅ Complete privacy, ✅ No API costs, ✅ Works offline
**Cons**: ❌ Needs powerful hardware, ❌ Slower responses

---

## 🏃 Running the Bot

### Development Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Run with auto-restart (install nodemon)
nodemon --exec python main.py
```

### Production Mode
```bash
# Run in background (Linux/macOS)
nohup python main.py > priya.log 2>&1 &

# Run as service (Windows)
# Use Task Scheduler or NSSM

# Run with process manager
pip install supervisor
# Configure supervisord.conf
```

### Monitoring
```bash
# Check logs
tail -f priya.log

# Monitor resources
htop  # Linux/macOS
# Task Manager (Windows)

# Check bot status in Discord
!status
```

---

## 📱 Usage Guide

### Basic Commands
```
!join     - Join voice channel
!leave    - Leave voice channel  
!status   - Show bot status
```

### Chat Features
- **Natural conversation**: Just talk normally
- **Mentions**: @Priya for guaranteed response
- **Voice chat**: Talk in voice channels
- **Media**: Send images, videos, links
- **Hinglish**: Mix English and Hindi naturally

### Voice Features
```
1. Join a voice channel
2. Type !join
3. Start talking - Priya listens and responds
4. Type !leave when done
```

### Personality Features
- **Relationship building**: Remembers conversations
- **Activity-based responses**: Different moods by time
- **Emotional responses**: Happy, sad, excited, etc.
- **Cultural context**: Indian personality with Hinglish

---

## 🔧 Advanced Configuration

### Performance Tuning
```env
# High-end system
MAX_CONCURRENT_REQUESTS=20
MAX_MEMORY_MB=1000
REQUEST_TIMEOUT=30

# Low-end system  
MAX_CONCURRENT_REQUESTS=3
MAX_MEMORY_MB=200
REQUEST_TIMEOUT=60
```

### API Key Management
```env
# Priority order (1 = highest)
# Local models (if available) = Priority 1-4
GROQ_API_KEY=key1           # Priority 5-6
TOGETHER_API_KEY=key2       # Priority 7-8
HUGGINGFACE_API_KEY=key3    # Priority 9
OPENROUTER_API_KEY=key4     # Priority 10
ANTHROPIC_API_KEY=key5      # Priority 11
COHERE_API_KEY=key6         # Priority 12
```

### Voice Configuration
```env
# Voice settings
VOICE_LOCK_TIMEOUT=30
STT_TIMEOUT=15
TTS_TIMEOUT=10
MAX_AUDIO_DURATION=60
```

---

## 🚨 Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check Discord token
# Make sure it's in .env file correctly
```

#### No Responses
```bash
# Check bot permissions in Discord
# Ensure "Message Content Intent" is enabled
# Check if bot can see the channel

# Check logs
tail -f priya.log
```

#### Voice Not Working
```bash
# Install FFmpeg
# Windows: Download from ffmpeg.org
# macOS: brew install ffmpeg  
# Linux: sudo apt install ffmpeg

# Check voice permissions
# Bot needs "Connect" and "Speak" permissions
```

#### High Memory Usage
```env
# Reduce memory limit
MAX_MEMORY_MB=200

# Use cloud-only mode
# Remove local models
```

#### Slow Responses
```bash
# Use cloud APIs only
# Don't install Ollama

# Or upgrade hardware
# Add more RAM/CPU
```

### Debug Mode
```env
LOG_LEVEL=DEBUG
```

### Getting Help
1. Check logs: `tail -f priya.log`
2. Use `!status` command in Discord
3. Check GitHub Issues
4. Join Discord support server

---

## 📊 Deployment Comparison

| Feature | Cloud-Only | Hybrid | Full Local |
|---------|------------|--------|-------------|
| **Setup Time** | 5 minutes | 15 minutes | 30 minutes |
| **Hardware** | Any | 8GB+ RAM | 16GB+ RAM |
| **Internet** | Required | Optional | Setup only |
| **Privacy** | Medium | High | Maximum |
| **Speed** | Fast | Fastest | Medium |
| **Cost** | Free* | Free | Free |
| **Reliability** | High | Highest | Medium |

*Free with API rate limits

---

## 🎯 Recommended Setups

### Personal Use (1-10 users)
- **Mode**: Hybrid
- **Hardware**: 8GB RAM, quad-core CPU
- **Models**: llama3.2 + 2-3 API keys
- **Cost**: Free

### Small Server (10-100 users)  
- **Mode**: Cloud-first hybrid
- **Hardware**: 16GB RAM, 8-core CPU
- **Models**: Multiple API keys + local backup
- **Cost**: $0-50/month

### Large Server (100+ users)
- **Mode**: Multi-provider cloud
- **Hardware**: 32GB RAM, dedicated server
- **Models**: All API keys + GPU acceleration
- **Cost**: $50-200/month

---

**🎉 You're ready to deploy Priya! Choose your mode and start chatting with your AI best friend!**