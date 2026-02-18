# 🤖 Priya Discord Bot - Complete Beginner's Guide

Meet Priya, your AI best friend who talks with you via voice using free local AI models! This guide will take you from zero to having your own AI voice bot running.

## 📋 Table of Contents
1. [What is Priya?](#what-is-priya)
2. [Prerequisites](#prerequisites)
3. [Quick Setup (5 minutes)](#quick-setup)
4. [Detailed Setup](#detailed-setup)
5. [How to Use Priya](#how-to-use-priya)
6. [Commands Reference](#commands-reference)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Features](#advanced-features)

## 🎯 What is Priya?

Priya is a Discord bot that:
- **Talks with voice** - She can speak and listen to you
- **Uses AI** - Powered by 20+ AI models (local + cloud)
- **Remembers conversations** - Persistent memory across sessions
- **Has personality** - Acts like a 23-year-old Indian best friend
- **Works offline** - Can run without internet using local models
- **Is completely free** - No subscription fees

## 🛠️ Prerequisites

### Required
- **Python 3.8+** - [Download here](https://python.org/downloads)
- **Discord Account** - [Create here](https://discord.com)
- **Discord Server** - Where you'll add the bot

### Optional (for better experience)
- **Ollama** - For local AI models [Download here](https://ollama.ai)
- **FFmpeg** - For voice features [Download here](https://ffmpeg.org)

## ⚡ Quick Setup (5 minutes)

### Step 1: Download the Bot
```bash
git clone https://github.com/your-repo/Bot-priya.git
cd Bot-priya
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Create Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Name it "Priya"
3. Go to "Bot" tab → Click "Add Bot"
4. Copy the **Token** (keep it secret!)
5. Enable "Message Content Intent"

### Step 4: Add Bot to Server
1. Go to "OAuth2" → "URL Generator"
2. Select "bot" scope
3. Select permissions: "Send Messages", "Connect", "Speak"
4. Copy URL and open in browser
5. Select your server and authorize

### Step 5: Configure Bot
Create `.env` file:
```env
DISCORD_TOKEN=your_bot_token_here
LOG_LEVEL=INFO
```

### Step 6: Run Bot
```bash
python main.py
```

🎉 **Done!** Your bot should be online in Discord!

## 📖 Detailed Setup

### 1. Python Installation

**Windows:**
1. Download Python from python.org
2. ✅ Check "Add Python to PATH"
3. Install normally

**Mac:**
```bash
brew install python
```

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. Project Setup

**Download Project:**
```bash
# Option 1: Git clone
git clone https://github.com/your-repo/Bot-priya.git
cd Bot-priya

# Option 2: Download ZIP
# Download and extract to folder
```

**Install Dependencies:**
```bash
# Install all required packages
pip install -r requirements.txt

# If you get permission errors on Linux/Mac:
pip install --user -r requirements.txt
```

### 3. Discord Bot Creation (Detailed)

**Create Application:**
1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Name: "Priya" (or any name you like)
4. Click "Create"

**Create Bot:**
1. Click "Bot" in left sidebar
2. Click "Add Bot" → "Yes, do it!"
3. Under "Token" click "Copy" (save this!)
4. Under "Privileged Gateway Intents":
   - ✅ Enable "Message Content Intent"
   - ✅ Enable "Server Members Intent" (optional)

**Get Invite Link:**
1. Click "OAuth2" → "URL Generator"
2. Scopes: ✅ "bot"
3. Bot Permissions:
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Connect (for voice)
   - ✅ Speak (for voice)
   - ✅ Use Voice Activity
4. Copy generated URL

**Add to Server:**
1. Open the copied URL in browser
2. Select your Discord server
3. Click "Authorize"
4. Complete captcha if prompted

### 4. Configuration Files

**Create `.env` file:**
```env
# Required
DISCORD_TOKEN=your_discord_bot_token_here

# Optional - AI API Keys (for cloud backup)
GROQ_API_KEY=your_groq_key_here
TOGETHER_API_KEY=your_together_key_here
HUGGINGFACE_API_KEY=your_hf_key_here

# Optional - Voice
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Settings
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
VOICE_LOCK_TIMEOUT=30
```

**Get API Keys (Optional but Recommended):**

1. **Groq (Fast AI)** - [groq.com](https://groq.com)
   - Sign up → API Keys → Create
   - Free tier: 100 requests/day

2. **Together AI** - [together.ai](https://together.ai)
   - Sign up → Settings → API Keys
   - Free tier: $25 credit

3. **Hugging Face** - [huggingface.co](https://huggingface.co)
   - Sign up → Settings → Access Tokens
   - Free tier: Unlimited

### 5. Local AI Setup (Optional)

**Install Ollama:**
- **Windows/Mac:** Download from [ollama.ai](https://ollama.ai)
- **Linux:** `curl -fsSL https://ollama.ai/install.sh | sh`

**Download AI Models:**
```bash
# Recommended model (3.2GB)
ollama pull llama3.2

# Alternative models
ollama pull mistral      # 4.1GB
ollama pull codellama    # 3.8GB
```

**Install FFmpeg (for voice):**
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org) → Add to PATH
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

## 🎮 How to Use Priya

### Text Chat
Simply type messages in any channel where Priya has access:

```
You: Hey Priya, how are you?
Priya: Hello yaar! I'm doing great! How's your day going?

You: What's the weather like?
Priya: I can't check weather directly, but I can chat about anything else! What would you like to talk about?
```

### Voice Chat
1. Join a voice channel
2. Type: `!join` or `!voice`
3. Priya joins and you can talk to her
4. Say "Priya" to get her attention
5. Type `!leave` when done

### Memory System
Priya remembers your conversations:
```
You: My favorite color is blue
Priya: Got it! I'll remember that your favorite color is blue.

[Later...]
You: What's my favorite color?
Priya: Your favorite color is blue! 💙
```

## 📝 Commands Reference

### Basic Commands
- `!help` - Show all commands
- `!status` - Bot status and uptime
- `!ping` - Check bot response time

### Voice Commands
- `!join` - Join your voice channel
- `!leave` - Leave voice channel
- `!voice` - Toggle voice mode

### Memory Commands
- `!memory` - Show conversation history
- `!forget` - Clear your memory
- `!remember <text>` - Save important info

### AI Commands
- `!models` - List available AI models
- `!switch <model>` - Switch AI model
- `!health` - Check AI model health

### Admin Commands (Server Owner Only)
- `!config` - Show bot configuration
- `!logs` - Show recent logs
- `!restart` - Restart bot (if hosted)

## 🔧 Troubleshooting

### Bot Won't Start

**Error: "Invalid Token"**
```
Solution: Check your DISCORD_TOKEN in .env file
- Make sure no extra spaces
- Token should be 70+ characters
- Regenerate token if needed
```

**Error: "Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install discord.py
```

**Error: "Permission denied"**
```bash
# Linux/Mac - use --user flag
pip install --user -r requirements.txt

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Bot Online But Not Responding

**Check Permissions:**
1. Bot has "Send Messages" permission
2. Bot can see the channel
3. "Message Content Intent" is enabled

**Check Configuration:**
```bash
# Test with debug logging
LOG_LEVEL=DEBUG python main.py
```

### Voice Not Working

**Install FFmpeg:**
- Download from [ffmpeg.org](https://ffmpeg.org)
- Add to system PATH
- Restart terminal/command prompt

**Check Voice Permissions:**
- Bot has "Connect" and "Speak" permissions
- You're in a voice channel when using `!join`

### AI Models Not Working

**Local Models (Ollama):**
```bash
# Check if Ollama is running
ollama list

# Pull model if missing
ollama pull llama3.2

# Check Ollama service
ollama serve
```

**Cloud Models:**
- Check API keys in `.env` file
- Verify API key validity
- Check internet connection

### Memory Issues

**Clear Corrupted Memory:**
```bash
# Delete memory files
rm -rf data/memory/  # Linux/Mac
rmdir /s data\memory  # Windows

# Restart bot
python main.py
```

## 🚀 Advanced Features

### Custom Personality
Edit `src/core/personality.py` to customize Priya's responses:
```python
# Add custom responses
CUSTOM_RESPONSES = {
    "greeting": ["Hey there!", "What's up!"],
    "goodbye": ["See you later!", "Bye bye!"]
}
```

### Plugin System
Create custom skills in `src/skills/`:
```python
# src/skills/weather_skill.py
async def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 25°C"
```

### Web Dashboard
Access at `http://localhost:8080` when bot is running:
- View conversation history
- Monitor bot performance
- Manage settings

### Backup & Restore
```bash
# Backup conversations
python -c "from src.utils.backup_system import BackupSystem; BackupSystem().create_backup()"

# Restore from backup
python -c "from src.utils.backup_system import BackupSystem; BackupSystem().restore_backup('backup_file.json')"
```

## 🎯 Next Steps

1. **Join Community:** [Discord Server Link]
2. **Read Advanced Guide:** `DEPLOYMENT_GUIDE.md`
3. **Contribute:** `CONTRIBUTING.md`
4. **Report Issues:** GitHub Issues

## 💡 Tips for Best Experience

1. **Use Local Models:** Install Ollama for faster responses
2. **Get API Keys:** Add 2-3 cloud providers for reliability
3. **Enable Voice:** Install FFmpeg for voice features
4. **Regular Backups:** Backup your conversation data
5. **Monitor Logs:** Check logs for any issues

---

**Need Help?** 
- 📖 Check other guides in this folder
- 🐛 Report bugs on GitHub
- 💬 Join our Discord community
- 📧 Contact support

**Enjoy chatting with Priya!** 🎉