# 🚀 Quick Start Guide - Get Priya Running in 5 Minutes

## Step 1: Download & Install
```bash
# Download project
git clone https://github.com/your-repo/Bot-priya.git
cd Bot-priya

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Create Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. "New Application" → Name: "Priya"
3. "Bot" tab → "Add Bot" → Copy **Token**
4. Enable "Message Content Intent"
5. "OAuth2" → "URL Generator" → Select "bot" + permissions
6. Use generated URL to add bot to your server

## Step 3: Configure
Create `.env` file:
```env
DISCORD_TOKEN=paste_your_token_here
LOG_LEVEL=INFO
```

## Step 4: Run
```bash
python main.py
```

## Step 5: Test
In Discord:
- Type: `Hey Priya!`
- Use: `!help` for commands
- Try: `!join` for voice chat

## 🎯 What Works Immediately
- ✅ Text chat with AI personality
- ✅ Memory system (remembers conversations)
- ✅ 20+ cloud AI models as backup
- ✅ Basic voice commands

## 🔧 Optional Upgrades

### For Local AI (Faster, Private)
```bash
# Install Ollama
# Windows/Mac: Download from ollama.ai
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Download AI model
ollama pull llama3.2
```

### For Voice Features
- Install FFmpeg from [ffmpeg.org](https://ffmpeg.org)
- Add to system PATH

### For Better AI (Optional API Keys)
Add to `.env`:
```env
GROQ_API_KEY=your_key_here          # groq.com (free)
TOGETHER_API_KEY=your_key_here      # together.ai (free $25)
HUGGINGFACE_API_KEY=your_key_here   # huggingface.co (free)
```

## 🆘 Common Issues

**Bot won't start?**
- Check DISCORD_TOKEN is correct
- Run: `pip install -r requirements.txt`

**Bot online but not responding?**
- Enable "Message Content Intent" in Discord Developer Portal
- Check bot has "Send Messages" permission

**Need help?**
- Read `BEGINNER_GUIDE.md` for detailed setup
- Check `TROUBLESHOOTING.md` for solutions

---
**That's it! Your AI friend Priya is ready to chat!** 🎉