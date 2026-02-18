# 🔑 API Keys Guide - Get Free AI Access

This guide shows you how to get free API keys for 20+ AI providers to make Priya smarter and more reliable.

## 🎯 Why API Keys?

**Without API Keys:**
- ❌ Only basic responses
- ❌ Limited AI capabilities
- ❌ No backup if local models fail

**With API Keys:**
- ✅ Access to 20+ AI models
- ✅ Automatic failover system
- ✅ Faster responses
- ✅ Better conversation quality

## 🚀 Quick Setup (Top 3 Providers)

### 1. Groq (Fastest AI) - FREE
**Why:** Ultra-fast responses (500ms), free tier
**Free Tier:** 100 requests/day

1. Go to [groq.com](https://groq.com)
2. Sign up with email
3. Go to "API Keys" → "Create API Key"
4. Copy key → Add to `.env`:
```env
GROQ_API_KEY=gsk_your_key_here
```

### 2. Together AI (High Quality) - FREE $25
**Why:** Best open-source models, $25 free credit
**Free Tier:** $25 credit (≈2500 requests)

1. Go to [together.ai](https://together.ai)
2. Sign up → Verify email
3. "Settings" → "API Keys" → "Create"
4. Copy key → Add to `.env`:
```env
TOGETHER_API_KEY=your_key_here
```

### 3. Hugging Face (Most Models) - FREE
**Why:** Largest collection of AI models, unlimited free
**Free Tier:** Unlimited (with rate limits)

1. Go to [huggingface.co](https://huggingface.co)
2. Sign up → Verify email
3. "Settings" → "Access Tokens" → "New token"
4. Name: "Priya Bot" → "Read" permission
5. Copy token → Add to `.env`:
```env
HUGGINGFACE_API_KEY=hf_your_token_here
```

## 🌟 All Available Providers

### Tier 1: Premium (Best Quality)
| Provider | Free Tier | Speed | Quality | Setup |
|----------|-----------|-------|---------|-------|
| **Groq** | 100/day | ⚡⚡⚡ | ⭐⭐⭐⭐ | [groq.com](https://groq.com) |
| **Together AI** | $25 credit | ⚡⚡ | ⭐⭐⭐⭐⭐ | [together.ai](https://together.ai) |
| **Anthropic** | $5 credit | ⚡⚡ | ⭐⭐⭐⭐⭐ | [console.anthropic.com](https://console.anthropic.com) |

### Tier 2: Reliable (Good Balance)
| Provider | Free Tier | Speed | Quality | Setup |
|----------|-----------|-------|---------|-------|
| **Hugging Face** | Unlimited* | ⚡ | ⭐⭐⭐⭐ | [huggingface.co](https://huggingface.co) |
| **Cohere** | 100/month | ⚡⚡ | ⭐⭐⭐⭐ | [cohere.ai](https://cohere.ai) |
| **Replicate** | $10 credit | ⚡ | ⭐⭐⭐ | [replicate.com](https://replicate.com) |

### Tier 3: Backup (Free Options)
| Provider | Free Tier | Speed | Quality | Setup |
|----------|-----------|-------|---------|-------|
| **OpenRouter** | $1 credit | ⚡⚡ | ⭐⭐⭐⭐ | [openrouter.ai](https://openrouter.ai) |
| **Perplexity** | 20/day | ⚡⚡ | ⭐⭐⭐ | [perplexity.ai](https://perplexity.ai) |
| **AI21** | 10K tokens/month | ⚡ | ⭐⭐⭐ | [ai21.com](https://ai21.com) |

*Rate limited but no hard daily limit

## 📝 Detailed Setup Instructions

### Groq (Recommended First)
```
1. Visit: https://groq.com
2. Click "Sign Up" → Use email/Google
3. Verify email if required
4. Dashboard → "API Keys" → "Create API Key"
5. Name: "Priya Bot"
6. Copy the key (starts with "gsk_")
7. Add to .env: GROQ_API_KEY=gsk_your_key_here
```

### Together AI (Recommended Second)
```
1. Visit: https://together.ai
2. "Get Started" → Sign up with email
3. Verify email (check spam folder)
4. Dashboard → "Settings" → "API Keys"
5. "Create new API Key" → Name: "Priya"
6. Copy key → Add to .env: TOGETHER_API_KEY=your_key_here
```

### Anthropic (Claude AI)
```
1. Visit: https://console.anthropic.com
2. Sign up → Verify email
3. "API Keys" → "Create Key"
4. Name: "Priya Bot"
5. Copy key → Add to .env: ANTHROPIC_API_KEY=sk-ant-your_key_here
```

### Hugging Face (Most Models)
```
1. Visit: https://huggingface.co
2. Sign up → Verify email
3. Profile → "Settings" → "Access Tokens"
4. "New token" → Name: "Priya" → Role: "Read"
5. Copy token → Add to .env: HUGGINGFACE_API_KEY=hf_your_token_here
```

### Cohere (Command Models)
```
1. Visit: https://cohere.ai
2. "Get Started" → Sign up
3. Dashboard → "API Keys" → "Create API Key"
4. Copy key → Add to .env: COHERE_API_KEY=your_key_here
```

### OpenRouter (Multiple Models)
```
1. Visit: https://openrouter.ai
2. Sign up with GitHub/Google
3. "Keys" → "Create Key"
4. Name: "Priya Bot"
5. Copy key → Add to .env: OPENROUTER_API_KEY=sk-or-your_key_here
```

## 🔧 Configuration

### Complete .env Example
```env
# Required
DISCORD_TOKEN=your_discord_token

# Tier 1 (Recommended)
GROQ_API_KEY=gsk_your_groq_key
TOGETHER_API_KEY=your_together_key
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key

# Tier 2 (Good backup)
HUGGINGFACE_API_KEY=hf_your_hf_token
COHERE_API_KEY=your_cohere_key
REPLICATE_API_TOKEN=r8_your_replicate_token

# Tier 3 (Extra backup)
OPENROUTER_API_KEY=sk-or-your_openrouter_key
PERPLEXITY_API_KEY=pplx-your_perplexity_key
AI21_API_KEY=your_ai21_key

# Voice (Optional)
ELEVENLABS_API_KEY=your_elevenlabs_key

# Settings
LOG_LEVEL=INFO
```

### Test Your Keys
```bash
# Start bot and check status
python main.py

# In Discord, test:
!health          # Shows which APIs are working
!models          # Lists available models
!switch groq     # Test specific provider
```

## 💰 Free Tier Limits

### Daily Limits
- **Groq:** 100 requests/day
- **Perplexity:** 20 requests/day
- **Cohere:** ~3 requests/day (100/month)

### Credit-Based
- **Together AI:** $25 free credit (≈2500 requests)
- **Anthropic:** $5 free credit (≈1000 requests)
- **OpenRouter:** $1 free credit (≈100 requests)
- **Replicate:** $10 free credit (varies by model)

### Unlimited (Rate Limited)
- **Hugging Face:** Unlimited but slower
- **AI21:** 10K tokens/month

## 🎯 Recommended Combinations

### Minimal Setup (2 keys)
```env
GROQ_API_KEY=your_groq_key          # Fast responses
HUGGINGFACE_API_KEY=your_hf_token   # Unlimited backup
```

### Balanced Setup (4 keys)
```env
GROQ_API_KEY=your_groq_key          # Speed
TOGETHER_API_KEY=your_together_key  # Quality
HUGGINGFACE_API_KEY=your_hf_token   # Backup
ANTHROPIC_API_KEY=your_anthropic_key # Premium
```

### Maximum Reliability (8+ keys)
```env
# Add all Tier 1 + Tier 2 providers
# Bot will automatically failover between them
```

## 🔍 Testing & Monitoring

### Check API Health
```
!health
```
Shows:
- ✅ Working APIs (green)
- ⚠️ Rate limited (yellow)  
- ❌ Failed APIs (red)
- Response times

### Switch Models
```
!models                    # List available
!switch groq              # Use Groq
!switch together          # Use Together AI
!switch anthropic         # Use Claude
```

### Monitor Usage
```
!status
```
Shows:
- Requests made today
- Successful vs failed
- Average response time
- Current active model

## 🚨 Troubleshooting

### Invalid API Key
```
Error: 401 Unauthorized
```
**Solutions:**
1. Check key is copied correctly (no spaces)
2. Verify key is active on provider website
3. Regenerate key if needed

### Rate Limit Hit
```
Error: 429 Too Many Requests
```
**Solutions:**
1. Wait for reset (usually 24 hours)
2. Add more API keys for automatic failover
3. Upgrade to paid plan

### API Not Responding
```
Error: Connection timeout
```
**Solutions:**
1. Check internet connection
2. Try different provider: `!switch huggingface`
3. Provider may be down (temporary)

## 💡 Pro Tips

### Maximize Free Usage
1. **Start with 3-4 providers** for good coverage
2. **Monitor usage** with `!health` command
3. **Rotate keys** when limits hit
4. **Use local models** (Ollama) as primary

### Best Performance
1. **Groq first** - Fastest responses
2. **Together AI second** - Best quality
3. **Hugging Face backup** - Never runs out

### Security
1. **Never share API keys** publicly
2. **Use environment variables** (`.env` file)
3. **Regenerate keys** if compromised
4. **Monitor usage** for unexpected activity

## 🎉 You're All Set!

With API keys configured:
- ✅ Priya has access to 20+ AI models
- ✅ Automatic failover if one provider fails
- ✅ Better conversation quality
- ✅ Faster response times

**Test it out:**
```
You: Hey Priya, tell me a joke!
Priya: Why don't scientists trust atoms? Because they make up everything! 😄
```

---

**Need help?** Check `TROUBLESHOOTING.md` or ask in our Discord community!