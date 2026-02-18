# Priya Discord Bot - Production Grade Architecture

Meet Priya, your intelligent 23-year-old Indian best friend who talks with you via voice using 100% free, unlimited local AI models. Now with **production-grade architecture** and **enterprise-level reliability**.

## 🏗️ Architecture Overview

### Modular Design
```
src/
├── config/          # Configuration management
├── core/           # Core personality & state
├── engines/        # Processing engines (voice, etc.)
├── models/         # AI model management
└── utils/          # Utilities (logging, concurrency)
```

### Key Features
- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **LLM Fallback System** - 20+ AI providers with automatic failover
- ✅ **Timeout Handling** - Robust timeout management for all operations
- ✅ **Concurrency Control** - Voice locks and request limiting
- ✅ **Memory Management** - Automatic cleanup and memory monitoring
- ✅ **Structured Logging** - JSON logs with performance metrics
- ✅ **Model Warmup** - Pre-load models on startup
- ✅ **Graceful Degradation** - Fallback responses when models fail
- ✅ **Type Hints** - Full type safety throughout codebase
- ✅ **Comprehensive Docstrings** - Documentation for all functions
- ✅ **No Function >70 Lines** - Clean, maintainable code
- ✅ **No File >400 Lines** - Proper modularization
- ✅ **100% Feature Parity** - All original functionality preserved

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
Create `.env` file:
```env
DISCORD_TOKEN=your_discord_token

# Optional API Keys (for cloud fallback)
GROQ_API_KEY=your_groq_key
TOGETHER_API_KEY=your_together_key
HUGGINGFACE_API_KEY=your_hf_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 3. Install Local Models (Optional)
```bash
# Install Ollama for local AI
ollama pull llama3.2

# Install FFmpeg for voice
# Download from https://ffmpeg.org and add to PATH
```

### 4. Run Bot
```bash
python main.py
```

## 🧠 AI Model System

### Local Models (Highest Priority)
- **Ollama**: llama3.2, llama3.1, mistral, codellama
- **Whisper**: Local speech recognition
- **Coqui TTS**: Local voice synthesis

### Cloud Fallback (20+ Providers)
- **Groq**: Ultra-fast inference
- **Together AI**: High-quality models
- **Hugging Face**: Open source models
- **Anthropic**: Claude models
- **Cohere**: Command models
- **OpenRouter**: Multiple providers
- **And 15+ more providers**

### Automatic Failover
1. Try local models first (if available)
2. Parallel requests to top 3 cloud providers
3. Return first successful response
4. Automatic health monitoring
5. Rate limit management
6. Emergency fallback responses

## 🎤 Voice Processing

### Speech-to-Text
- **Local**: faster-whisper (offline)
- **Cloud**: Groq Whisper API
- **Features**: Multi-language, auto-detection

### Text-to-Speech
- **Local**: Coqui TTS (multilingual)
- **Cloud**: ElevenLabs (emotional voices)
- **Features**: 50+ emotions, Indian accent

## 📊 Monitoring & Logging

### Structured Logging
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "module": "llm_fallback",
  "function": "generate_response",
  "message": "Request completed",
  "user_id": "123456789",
  "model": "groq_llama32",
  "duration_ms": 1250,
  "success": true
}
```

### Performance Metrics
- Request latency tracking
- Model success rates
- Memory usage monitoring
- Error rate analysis
- Concurrent request limits

## 🔧 Configuration

### Environment Variables
```env
# Required
DISCORD_TOKEN=your_token

# Logging
LOG_LEVEL=INFO
LOG_FILE=priya.log

# Performance
MAX_CONCURRENT_REQUESTS=10
VOICE_LOCK_TIMEOUT=30
REQUEST_TIMEOUT=45
MAX_MEMORY_MB=500
```

### Model Configuration
```python
# In src/config/settings.py
@dataclass
class ModelConfig:
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.95
    max_tokens: int = 200
```

## 🛡️ Error Handling

### Timeout Management
- Function-level timeouts with decorators
- Configurable timeout values
- Graceful timeout handling

### Retry Logic
- Exponential backoff
- Configurable retry attempts
- Circuit breaker pattern

### Graceful Degradation
- Fallback responses when all models fail
- Partial functionality during outages
- User-friendly error messages

## 🔄 Concurrency Control

### Voice Channel Locking
```python
async with concurrency_manager.voice_exclusive(user_id):
    # Exclusive voice channel access
    voice_client = await channel.connect()
```

### Request Rate Limiting
```python
async with concurrency_manager.request_slot(user_id, "message"):
    # Process message with concurrency control
    response = await generate_response(message)
```

## 💾 Memory Management

### Automatic Cleanup
- Old conversation data removal
- Memory usage monitoring
- Configurable cleanup intervals
- Garbage collection optimization

### Data Persistence
- JSON-based storage
- Atomic file operations
- Backup and recovery
- Data migration support

## 🧪 Testing & Development

### Run Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
```

### Type Checking
```bash
mypy src/
```

## 📈 Performance Benchmarks

### Response Times
- Local models: 500-2000ms
- Cloud models: 1000-3000ms
- Voice processing: 2000-5000ms

### Throughput
- Concurrent requests: 10 (configurable)
- Messages per minute: 100+
- Voice connections: Multiple servers

### Resource Usage
- Memory: <500MB (configurable)
- CPU: Moderate (depends on local models)
- Network: Minimal (cloud fallback only)

## 🔍 Monitoring Commands

### Bot Status
```
!status
```
Shows:
- Uptime and message counts
- Available AI providers
- Voice engine status
- Active requests
- Memory usage

### Health Check
```
!health
```
Shows:
- Model provider health
- Response times
- Error rates
- System metrics

## 🚨 Troubleshooting

### Common Issues

1. **Models not responding**
   - Check API keys in `.env`
   - Verify internet connection
   - Check logs for specific errors

2. **Voice not working**
   - Install FFmpeg
   - Check voice permissions
   - Verify audio file formats

3. **High memory usage**
   - Reduce `MAX_MEMORY_MB` in config
   - Enable automatic cleanup
   - Monitor conversation history size

4. **Slow responses**
   - Check model provider status
   - Increase timeout values
   - Use local models for faster responses

### Debug Mode
```env
LOG_LEVEL=DEBUG
```

## 🔮 Future Enhancements

- [ ] Redis caching layer
- [ ] Kubernetes deployment
- [ ] Prometheus metrics
- [ ] GraphQL API
- [ ] WebSocket real-time updates
- [ ] Multi-language UI
- [ ] Advanced analytics dashboard

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request

## 💬 Support

- GitHub Issues: Bug reports and feature requests
- Discord Server: Community support
- Documentation: Comprehensive guides

---

**Priya** - Your AI best friend, now with enterprise-grade reliability! 🚀✨