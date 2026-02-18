# 🔑 API Keys Guide - Get 18,300+ FREE Requests Daily

## 🚀 Quick Setup (5 minutes)
Get these 3 keys for best reliability:

### 1. Groq (6,000 requests/day) ⭐ RECOMMENDED
- **Website**: https://console.groq.com
- **Steps**: Sign up → API Keys → Create Key
- **Speed**: Ultra-fast (500ms responses)
- **Models**: Llama 3.2, Llama 3.1, Mixtral

### 2. Together AI (1,000 requests/day) ⭐ RECOMMENDED  
- **Website**: https://api.together.xyz
- **Steps**: Sign up → Settings → API Keys
- **Quality**: High-quality models
- **Models**: Llama, Mistral, Code models

### 3. Hugging Face (10,000 requests/day) ⭐ RECOMMENDED
- **Website**: https://huggingface.co/settings/tokens
- **Steps**: Sign up → Settings → Access Tokens → New Token
- **Variety**: Largest model selection
- **Models**: 100+ open source models

## 🎯 Additional Providers (Optional)

### 4. OpenRouter (200 requests/day)
- **Website**: https://openrouter.ai
- **Steps**: Sign up → Keys → Create Key
- **Feature**: Access to multiple providers

### 5. Anthropic Claude (100 requests/day)
- **Website**: https://console.anthropic.com
- **Steps**: Sign up → API Keys → Create Key
- **Quality**: Excellent reasoning

### 6. Cohere (1,000 requests/day)
- **Website**: https://cohere.ai
- **Steps**: Sign up → API Keys → Create Key
- **Feature**: Good for chat

## 🎤 Voice APIs (Optional)

### ElevenLabs (10,000 chars/month FREE)
- **Website**: https://elevenlabs.io
- **Steps**: Sign up → Profile → API Key
- **Feature**: Realistic voice synthesis
- **Quality**: Best emotional voices

## 📊 Total FREE Capacity

| Provider | Daily Limit | Speed | Quality |
|----------|-------------|-------|---------|
| Groq | 6,000 | ⚡ Ultra Fast | 🟢 Good |
| HuggingFace | 10,000 | 🟡 Medium | 🟢 Good |
| Together AI | 1,000 | ⚡ Fast | 🟢 High |
| OpenRouter | 200 | 🟡 Medium | 🟢 Good |
| Anthropic | 100 | 🟡 Medium | 🟢 Excellent |
| Cohere | 1,000 | 🟡 Medium | 🟢 Good |
| **TOTAL** | **18,300+** | | |

## 🔧 Setup Instructions

### 1. Get API Keys
Visit the websites above and create accounts

### 2. Add to .env file
```env
DISCORD_TOKEN=your_discord_token

# Add your API keys here
GROQ_API_KEY=gsk_your_groq_key_here
TOGETHER_API_KEY=your_together_key_here
HUGGINGFACE_API_KEY=hf_your_huggingface_token_here
OPENROUTER_API_KEY=sk-or-your_openrouter_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
COHERE_API_KEY=your_cohere_key_here

# Voice (optional)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### 3. Test Setup
```bash
python main.py
# Bot will automatically detect and use available keys
```

## 💡 Pro Tips

### Minimum Setup (Works Great)
Just get these 2 keys:
- ✅ Groq (6,000 requests)
- ✅ HuggingFace (10,000 requests)
- **Total**: 16,000 requests/day

### Recommended Setup
Get these 3 keys:
- ✅ Groq (6,000 requests)
- ✅ HuggingFace (10,000 requests)  
- ✅ Together AI (1,000 requests)
- **Total**: 17,000 requests/day

### Maximum Setup
Get all 6 keys:
- **Total**: 18,300+ requests/day
- **Reliability**: Maximum fallback options

## 🔒 Security Best Practices

### Keep Keys Secret
- ❌ Never commit .env to git
- ❌ Never share keys publicly
- ✅ Use environment variables
- ✅ Regenerate if compromised

### Rate Limiting
- Bot automatically manages rate limits
- Switches providers when limits hit
- Resets daily at midnight UTC

## 🚨 Troubleshooting

### Key Not Working
1. Check key format (each provider has different format)
2. Verify account is activated
3. Check rate limits haven't been exceeded
4. Regenerate key if needed

### No Responses
1. Check at least one key is working
2. Verify internet connection
3. Check logs: `tail -f priya.log`
4. Use `!status` command in Discord

### Rate Limited
- Bot automatically switches to next provider
- Wait for daily reset (midnight UTC)
- Add more API keys for higher limits

## 📈 Usage Monitoring

### Check Status
```
!status
```
Shows:
- Available providers
- Rate limit status
- Response times
- Error rates

### View Logs
```bash
tail -f priya.log
```
Shows:
- Which provider was used
- Response times
- Any errors

---

**🎉 With these free API keys, you get 18,300+ requests per day - enough for thousands of conversations!**