#!/usr/bin/env python3
"""
Priya Bot - Quick Setup Script
Automatically configures the bot based on your preferences
"""
import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("🤖" + "="*50)
    print("   PRIYA DISCORD BOT - QUICK SETUP")
    print("="*52)
    print()

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current:", sys.version)
        sys.exit(1)
    print("✅ Python version:", sys.version.split()[0])

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def setup_environment():
    """Setup environment file"""
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if example_file.exists():
        # Copy example to .env
        with open(example_file) as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ Created .env file from template")
    else:
        # Create basic .env
        content = """# Priya Discord Bot Configuration
DISCORD_TOKEN=your_discord_token_here
GROQ_API_KEY=
TOGETHER_API_KEY=
HUGGINGFACE_API_KEY=
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ Created basic .env file")

def get_setup_mode():
    """Get user's preferred setup mode"""
    print("\n🚀 Choose your setup mode:")
    print("1. Cloud-Only (Easiest - works anywhere)")
    print("2. Hybrid (Recommended - local + cloud)")  
    print("3. Full Local (Privacy - local only)")
    
    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        if choice in ['1', '2', '3']:
            return int(choice)
        print("Please enter 1, 2, or 3")

def setup_cloud_mode():
    """Setup cloud-only mode"""
    print("\n☁️ Setting up Cloud-Only mode...")
    print("✅ No additional setup needed")
    print("📝 Next steps:")
    print("   1. Edit .env file with your Discord token")
    print("   2. Add 2-3 API keys (Groq, Together, HuggingFace)")
    print("   3. Run: python main.py")

def setup_hybrid_mode():
    """Setup hybrid mode"""
    print("\n🔄 Setting up Hybrid mode...")
    
    # Check if Ollama is installed
    try:
        subprocess.check_call(["ollama", "--version"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print("✅ Ollama is already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama not found")
        print("📥 Please install Ollama:")
        print("   Windows/macOS: Download from https://ollama.ai")
        print("   Linux: curl -fsSL https://ollama.ai/install.sh | sh")
        return
    
    # Pull recommended model
    print("📥 Pulling recommended model (llama3.2)...")
    try:
        subprocess.check_call(["ollama", "pull", "llama3.2"])
        print("✅ Model downloaded successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to download model")
        print("   Try manually: ollama pull llama3.2")
    
    print("📝 Next steps:")
    print("   1. Edit .env file with your Discord token")
    print("   2. Add 1-2 API keys for backup (optional)")
    print("   3. Run: python main.py")

def setup_local_mode():
    """Setup full local mode"""
    print("\n🏠 Setting up Full Local mode...")
    
    # Check Ollama
    try:
        subprocess.check_call(["ollama", "--version"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print("✅ Ollama is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Ollama not found - required for local mode")
        return
    
    # Pull multiple models
    models = ["llama3.2", "mistral"]
    for model in models:
        print(f"📥 Pulling {model}...")
        try:
            subprocess.check_call(["ollama", "pull", model])
            print(f"✅ {model} downloaded")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to download {model}")
    
    # Check FFmpeg for voice
    try:
        subprocess.check_call(["ffmpeg", "-version"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print("✅ FFmpeg is installed (voice support)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ FFmpeg not found (voice features disabled)")
        print("   Install from: https://ffmpeg.org")
    
    print("📝 Next steps:")
    print("   1. Edit .env file with your Discord token")
    print("   2. Run: python main.py")

def main():
    print_banner()
    
    # Check requirements
    check_python()
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment
    setup_environment()
    
    # Get setup mode
    mode = get_setup_mode()
    
    # Setup based on mode
    if mode == 1:
        setup_cloud_mode()
    elif mode == 2:
        setup_hybrid_mode()
    elif mode == 3:
        setup_local_mode()
    
    print("\n🎉 Setup complete!")
    print("📖 See DEPLOYMENT_GUIDE.md for detailed instructions")
    print("🚀 Run 'python main.py' to start the bot")

if __name__ == "__main__":
    main()