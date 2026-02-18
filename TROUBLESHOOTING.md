# 🔧 Troubleshooting Guide

## 🚨 Bot Won't Start

### Error: "Invalid Token"
```
discord.errors.LoginFailure: Improper token has been passed.
```
**Solutions:**
1. Check `.env` file has correct `DISCORD_TOKEN`
2. No spaces before/after token
3. Token should be 70+ characters
4. Regenerate token in Discord Developer Portal if needed

### Error: "Module not found"
```
ModuleNotFoundError: No module named 'discord'
```
**Solutions:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Or install specific missing module
pip install discord.py aiohttp

# If permission issues (Linux/Mac)
pip install --user -r requirements.txt
```

### Error: "Permission denied"
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## 🤖 Bot Online But Not Responding

### Check Discord Permissions
1. **Developer Portal:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Select your bot → "Bot" tab
   - ✅ Enable "Message Content Intent"
   - ✅ Enable "Server Members Intent" (optional)

2. **Server Permissions:**
   - Bot has "Send Messages" permission
   - Bot can see the channel you're typing in
   - Bot role is above other roles (if using role permissions)

### Test Bot Response
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py

# Check if bot receives messages
# Look for logs like: "Received message from user..."
```

### Check Bot Status
In Discord, type:
```
!status
!ping
!health
```

## 🎤 Voice Features Not Working

### FFmpeg Not Installed
```
Error: ffmpeg not found
```
**Solutions:**
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org) → Extract → Add to PATH
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

**Test FFmpeg:**
```bash
ffmpeg -version
# Should show version info
```

### Voice Permissions Missing
**Check Discord Permissions:**
- ✅ Connect
- ✅ Speak  
- ✅ Use Voice Activity

**Test Voice:**
1. Join a voice channel
2. Type `!join`
3. Bot should join your channel

### Voice Channel Issues
```
Error: Already connected to a voice channel
```
**Solutions:**
```
!leave          # Leave current channel
!join           # Join your channel
```

## 🧠 AI Models Not Working

### Local Models (Ollama)

**Ollama Not Running:**
```bash
# Check if Ollama is installed
ollama --version

# Start Ollama service
ollama serve

# List available models
ollama list

# Pull missing model
ollama pull llama3.2
```

**Model Not Found:**
```
Error: model 'llama3.2' not found
```
**Solutions:**
```bash
# Pull the model
ollama pull llama3.2

# Or try alternative
ollama pull mistral
ollama pull codellama
```

### Cloud Models (API Keys)

**Invalid API Key:**
```
Error: 401 Unauthorized
```
**Solutions:**
1. Check API key in `.env` file
2. Verify key is valid (test on provider website)
3. Check key has correct permissions

**Rate Limit Exceeded:**
```
Error: 429 Too Many Requests
```
**Solutions:**
1. Wait a few minutes
2. Add more API keys to `.env`
3. Upgrade to paid plan

**Test API Keys:**
```bash
# Test Groq
curl -H "Authorization: Bearer YOUR_GROQ_KEY" https://api.groq.com/openai/v1/models

# Test Together
curl -H "Authorization: Bearer YOUR_TOGETHER_KEY" https://api.together.xyz/models
```

## 💾 Memory & Data Issues

### Memory Corruption
```
Error: Failed to load conversation history
```
**Solutions:**
```bash
# Clear corrupted memory (WARNING: Loses chat history)
rm -rf data/memory/        # Linux/Mac
rmdir /s /q data\memory    # Windows

# Restart bot
python main.py
```

### Database Locked
```
Error: database is locked
```
**Solutions:**
1. Stop bot completely
2. Wait 10 seconds
3. Restart bot

### Backup & Restore
```bash
# Create backup before fixing issues
python -c "from src.utils.backup_system import BackupSystem; BackupSystem().create_backup()"

# Restore if needed
python -c "from src.utils.backup_system import BackupSystem; BackupSystem().restore_backup('backup_2024_01_01.json')"
```

## 🔧 Performance Issues

### High Memory Usage
```
Warning: Memory usage above 500MB
```
**Solutions:**
1. Reduce `MAX_MEMORY_MB` in `.env`
2. Clear old conversations: `!forget`
3. Restart bot periodically

### Slow Responses
**Check Model Performance:**
```
!health         # Shows model response times
!models         # Lists available models
!switch groq    # Switch to faster model
```

**Optimize Settings:**
```env
# In .env file
MAX_CONCURRENT_REQUESTS=5    # Reduce if overloaded
REQUEST_TIMEOUT=30           # Increase if timeouts
VOICE_LOCK_TIMEOUT=20        # Reduce for faster voice
```

## 🌐 Network Issues

### Connection Timeout
```
Error: Connection timeout
```
**Solutions:**
1. Check internet connection
2. Try different AI provider
3. Increase timeout in `.env`:
```env
REQUEST_TIMEOUT=60
```

### Firewall Blocking
**Windows Firewall:**
1. Windows Security → Firewall
2. Allow Python through firewall

**Corporate Network:**
- May block Discord or AI APIs
- Try from personal network

## 📊 Logging & Debugging

### Enable Debug Logging
```env
# In .env file
LOG_LEVEL=DEBUG
```

### Check Log Files
```bash
# View recent logs
tail -f priya.log          # Linux/Mac
Get-Content priya.log -Tail 50 -Wait  # Windows PowerShell
```

### Common Log Messages
```
INFO: Bot started successfully
ERROR: Failed to connect to voice channel
WARNING: API rate limit approaching
DEBUG: Received message: "Hello Priya"
```

## 🆘 Emergency Fixes

### Complete Reset
```bash
# 1. Stop bot (Ctrl+C)

# 2. Clear all data (WARNING: Loses everything)
rm -rf data/               # Linux/Mac
rmdir /s /q data           # Windows

# 3. Reset config
cp .env.example .env
# Edit .env with your Discord token

# 4. Reinstall dependencies
pip install -r requirements.txt

# 5. Restart
python main.py
```

### Factory Reset
```bash
# Download fresh copy
git clone https://github.com/your-repo/Bot-priya.git Bot-priya-fresh
cd Bot-priya-fresh

# Copy your .env
cp ../Bot-priya/.env .

# Install and run
pip install -r requirements.txt
python main.py
```

## 📞 Getting Help

### Self-Diagnosis
```
!status     # Bot health check
!health     # AI models status  
!config     # Current settings
!logs       # Recent errors
```

### Log Collection
```bash
# Collect logs for support
python -c "
import json
from src.utils.logging import get_recent_logs
logs = get_recent_logs(100)
with open('debug_logs.json', 'w') as f:
    json.dump(logs, f, indent=2)
print('Logs saved to debug_logs.json')
"
```

### Support Channels
1. **GitHub Issues:** Bug reports with logs
2. **Discord Community:** Quick help
3. **Documentation:** Check other .md files

### Before Asking for Help
1. ✅ Check this troubleshooting guide
2. ✅ Enable debug logging
3. ✅ Collect error messages
4. ✅ Note what you were doing when error occurred
5. ✅ Try basic fixes (restart, reinstall)

---

**Most issues are solved by:**
1. Checking Discord permissions
2. Verifying API keys
3. Restarting the bot
4. Reinstalling dependencies

**Still stuck? We're here to help!** 🤝