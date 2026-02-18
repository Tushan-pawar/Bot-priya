# System Requirements & Installation Guide

## 💻 System Requirements

### Minimum (Cloud-Only)
- **RAM**: 2GB
- **Storage**: 1GB
- **CPU**: Dual-core
- **Python**: 3.8+
- **Internet**: Required

### Recommended (Hybrid)
- **RAM**: 8GB
- **Storage**: 10GB
- **CPU**: Quad-core
- **Python**: 3.10+
- **Internet**: Broadband

### Optimal (Full Local)
- **RAM**: 16GB+
- **Storage**: 50GB+ SSD
- **CPU**: 8+ cores
- **GPU**: 8GB+ VRAM (optional)
- **Python**: 3.11+

## 🚀 Quick Installation

### 1. Install Python
```bash
# Windows: Download from python.org
# macOS: brew install python
# Ubuntu: sudo apt install python3.11 python3.11-pip
```

### 2. Clone & Setup
```bash
git clone <repo-url>
cd Bot-priya
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Discord token
```

### 4. Run Bot
```bash
python main.py
```

## 🧠 Local AI Setup (Optional)

### Install Ollama
```bash
# Windows/macOS: Download from ollama.ai
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.2      # 2GB
ollama pull llama3.1      # 4.7GB  
ollama pull mistral       # 4.1GB
```

### Install Voice Models (Optional)
```bash
# FFmpeg for audio processing
# Windows: Download from ffmpeg.org
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg

# Python packages installed automatically
pip install faster-whisper TTS
```

## 📊 Resource Usage

### Cloud-Only Mode
- **RAM**: 100-300MB
- **CPU**: 5-15%
- **Storage**: 500MB
- **Network**: 1-10MB/hour

### Hybrid Mode  
- **RAM**: 200-500MB
- **CPU**: 10-30%
- **Storage**: 2-5GB
- **Network**: 0.5-5MB/hour

### Full Local Mode
- **RAM**: 2-8GB (depends on models)
- **CPU**: 20-80% (during inference)
- **Storage**: 10-50GB
- **Network**: Minimal

## ⚡ Performance Expectations

### Response Times
- **Cloud APIs**: 1-3 seconds
- **Local CPU**: 2-10 seconds
- **Local GPU**: 0.5-2 seconds

### Throughput
- **Cloud**: 100+ messages/minute
- **Local**: 10-60 messages/minute

## 🔧 Optimization Tips

### For Low-End Systems
```env
# In .env file
MAX_CONCURRENT_REQUESTS=3
MAX_MEMORY_MB=200
REQUEST_TIMEOUT=60
```

### For High-End Systems
```env
MAX_CONCURRENT_REQUESTS=20
MAX_MEMORY_MB=1000
REQUEST_TIMEOUT=30
```

## 🚨 Troubleshooting

### Common Issues
1. **Out of Memory**: Reduce MAX_MEMORY_MB
2. **Slow Responses**: Use cloud APIs only
3. **Model Download Fails**: Check internet connection
4. **Voice Issues**: Install FFmpeg properly

### Platform-Specific

#### Windows
- Install Visual C++ Redistributable
- Add Python to PATH
- Use PowerShell as admin

#### macOS
- Install Xcode Command Line Tools
- Use Homebrew for dependencies
- Grant microphone permissions

#### Linux
- Install build-essential
- Configure audio permissions
- Use virtual environments