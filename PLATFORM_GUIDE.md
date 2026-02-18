# 🚀 Priya AI Assistant Platform - Integration Guide

## 📁 New Modular Architecture

```
Bot-Priya/
├── src/
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py      # Environment & model configs
│   ├── core/               # Core personality & state
│   │   ├── __init__.py
│   │   └── personality.py   # Activity engine, memory, personality
│   ├── engines/            # Processing engines
│   │   ├── __init__.py
│   │   └── voice.py        # Voice processing with fallback
│   ├── models/             # AI model management
│   │   ├── __init__.py
│   │   └── llm_fallback.py # Multi-provider LLM system
│   ├── memory/             # NEW: Persistent memory system
│   │   ├── __init__.py
│   │   └── persistent_memory.py # SQLite + FAISS vector search
│   ├── voice/              # NEW: Real-time voice streaming
│   │   ├── __init__.py
│   │   └── streaming_voice.py # Streaming STT/TTS with interruption
│   ├── skills/             # NEW: Plugin/skill architecture
│   │   ├── __init__.py
│   │   ├── skill_manager.py # Dynamic skill loading
│   │   └── example_skills.py # Summarize, code review, etc.
│   ├── discord_integration/ # NEW: Discord native features
│   │   ├── __init__.py
│   │   └── native_features.py # Slash commands, roles, auto-join
│   ├── dashboard/          # NEW: Web admin dashboard
│   │   ├── __init__.py
│   │   ├── admin_dashboard.py # FastAPI dashboard
│   │   └── templates/      # HTML templates
│   └── utils/              # Utilities
│       ├── __init__.py
│       ├── concurrency.py  # Concurrency control
│       ├── helpers.py      # Helper functions
│       ├── logging.py      # Structured logging
│       ├── types.py        # Type definitions
│       └── optimization_logger.py # NEW: Self-optimization
├── data/                   # NEW: Data storage
│   ├── memory.db          # SQLite database
│   └── optimization/      # Optimization logs
├── main.py                # NEW: Clean entry point
├── requirements.txt       # Updated dependencies
└── README.md             # Updated documentation
```

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```env
# .env file
DISCORD_TOKEN=your_discord_token

# AI API Keys (optional)
GROQ_API_KEY=your_groq_key
TOGETHER_API_KEY=your_together_key
HUGGINGFACE_API_KEY=your_hf_key

# Dashboard Security
ADMIN_TOKEN=your-secure-admin-token-here
```

### 3. Run the Platform
```bash
python main.py
```

## 🧠 New Features Overview

### 1. Persistent Memory System
- **SQLite Database**: Stores all conversations
- **FAISS Vector Search**: Semantic memory retrieval
- **Per-user Memory**: Individual memory for each user
- **Server-level Memory**: Optional server-wide memory

```python
# Usage example
await memory_system.save_memory(
    user_id="123456789",
    content="User loves pizza and gaming",
    server_id="987654321",
    importance=0.8
)

memories = await memory_system.retrieve_memory(
    user_id="123456789",
    query="what does user like?",
    limit=5
)
```

### 2. Real-Time Voice Streaming
- **Streaming STT**: Real-time speech recognition
- **Interruptible TTS**: Stop speaking when user talks
- **VAD**: Voice Activity Detection
- **Partial Transcripts**: Live transcription updates

```python
# Voice callbacks
streaming_voice.on_speech_start = handle_speech_start
streaming_voice.on_final_transcript = handle_transcript
await streaming_voice.start_listening(user_id)
```

### 3. Plugin/Skill Architecture
- **Dynamic Loading**: Auto-load skills from `/skills` directory
- **Base Class**: Inherit from `BaseSkill`
- **Trigger System**: Keyword-based skill activation
- **Context Passing**: Rich context for skill execution

```python
# Create a new skill
class MySkill(BaseSkill):
    @property
    def name(self) -> str:
        return "my_skill"
    
    @property
    def triggers(self) -> List[str]:
        return ["my trigger", "activate skill"]
    
    async def execute(self, context: SkillContext) -> str:
        return "Skill executed!"
```

### 4. Discord Native Integration
- **Slash Commands**: `/memory`, `/personality`, `/skills`
- **Role-based Behavior**: Different responses per role
- **Auto-join Voice**: Automatically join voice channels
- **Per-channel Personality**: Channel-specific configurations

```python
# Slash command usage
/memory query:what did we talk about yesterday?
/personality mode:savage
/skills  # List all available skills
```

### 5. Web Admin Dashboard
- **Real-time Monitoring**: Live stats and logs
- **Memory Management**: View and search memories
- **User Analytics**: Active users and statistics
- **Personality Control**: Change modes remotely
- **Skill Management**: Reload skills dynamically

Access at: `http://127.0.0.1:8080`

### 6. Dynamic Personality Modes
- **Calm**: Peaceful and zen-like responses
- **Savage**: Witty and sarcastic banter
- **Motivational**: Energetic and inspiring
- **Study**: Focused on productivity
- **Corporate**: Professional and efficient

```python
# Change personality per server
discord_integration.personality_modes[server_id] = "savage"
```

### 7. Self-Optimization Logging
- **Failed Response Tracking**: Log and analyze failures
- **Unclear Query Detection**: Identify low-confidence responses
- **Pattern Analysis**: Automatic insight generation
- **Optimization Reports**: Detailed performance reports

## 🎯 Usage Examples

### Memory System
```python
# Save important information
await memory_system.save_memory(
    user_id="123",
    content="User is studying computer science at MIT",
    importance=0.9
)

# Retrieve relevant memories
memories = await memory_system.retrieve_memory(
    user_id="123",
    query="what is user studying?",
    limit=3
)
```

### Skills System
```python
# Execute skill manually
context = SkillContext(
    user_id="123",
    message="summarize our conversation",
    # ... other context
)
result = await skill_manager.execute_skill("summarize", context)
```

### Voice Streaming
```python
# Start listening
await streaming_voice.start_listening(user_id)

# Speak with interruption support
await streaming_voice.speak_with_interruption(
    "Hello! I can be interrupted.",
    voice_client,
    voice_settings
)
```

## 🔧 Configuration

### Memory System
```python
# In persistent_memory.py
memory_system = MemorySystem(
    db_path="data/memory.db",
    vector_dim=384
)
```

### Voice Processing
```python
# In streaming_voice.py
streaming_voice = StreamingVoiceEngine()
streaming_voice.sample_rate = 16000
streaming_voice.chunk_size = 320
```

### Dashboard
```python
# In admin_dashboard.py
admin_dashboard = AdminDashboard(port=8080)
```

## 🚀 Running the Platform

### Development Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python main.py
```

### Production Mode
```bash
# Run with optimizations
python main.py
```

### Dashboard Only
```bash
# Run just the dashboard
python -c "
import asyncio
from src.dashboard.admin_dashboard import admin_dashboard
asyncio.run(admin_dashboard.start())
"
```

## 📊 Monitoring & Analytics

### Dashboard Features
- **System Stats**: Memory usage, active users, uptime
- **Memory Browser**: Search and view conversation memories
- **User Analytics**: User activity and engagement metrics
- **Skill Management**: Load/reload skills dynamically
- **Personality Control**: Change bot personality modes
- **Optimization Reports**: Performance insights and recommendations

### API Endpoints
- `GET /api/stats` - System statistics
- `GET /api/memories` - Memory entries
- `GET /api/users` - User analytics
- `POST /api/personality` - Change personality mode
- `GET /api/skills` - Skill information

## 🛠️ Extending the Platform

### Adding New Skills
1. Create file in `src/skills/`
2. Inherit from `BaseSkill`
3. Implement required methods
4. Skills auto-load on startup

### Adding New Memory Types
1. Extend `MemorySystem` class
2. Add new metadata fields
3. Create specialized retrieval methods

### Adding New Voice Features
1. Extend `StreamingVoiceEngine`
2. Add new callback types
3. Implement custom processing

## 🔒 Security Considerations

### Dashboard Security
- **Token Authentication**: Secure admin token required
- **HTTPS**: Use reverse proxy for production
- **Rate Limiting**: Implement request limits

### Memory Privacy
- **Per-user Isolation**: Users can't access others' memories
- **Data Encryption**: Consider encrypting sensitive data
- **Retention Policies**: Automatic cleanup of old data

## 🎉 Migration from Old System

The new system maintains **100% compatibility** with existing functionality while adding powerful new features:

1. **All original features preserved**
2. **Same Discord commands work**
3. **Existing personality intact**
4. **Voice chat still works**
5. **API fallback system enhanced**

Simply replace your old files with the new modular system and run `python main.py`!

---

**🚀 Your Priya AI Assistant is now a full-featured, modular AI platform with enterprise-grade capabilities!**