"""Main Discord bot with production-grade architecture."""
import discord
from discord.ext import commands
import asyncio
import os
import random
import traceback
from datetime import datetime
from typing import Dict, Optional, Any

from .config.settings import config
from .utils.logging import logger, perf_logger
from .utils.concurrency import concurrency_manager, with_timeout
from .core.personality import priya_core
from .models.llm_fallback import llm_system
from .engines.voice import voice_engine
from .memory.context_compression import context_compressor

# Constants
SEPARATOR_LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

class PriyaBot(commands.Bot):
    """Production-grade Priya Discord bot."""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        
        # Voice connections and state
        self.voice_connections: Dict[int, discord.VoiceClient] = {}
        self.voice_users: Dict[int, str] = {}  # guild_id -> user_id
        
        # Performance tracking
        self.start_time = datetime.now()
        self.message_count = 0
        self.response_count = 0
        
        # Model warmup flag
        self.models_warmed = False
        
    async def setup_hook(self):
        """Setup hook called when bot starts."""
        logger.info("Starting Priya bot setup...")
        
        # Warm up models
        await self._warmup_models()
        
        # Start background tasks
        self.loop.create_task(self._background_maintenance())
        
        logger.info("Priya bot setup completed")
    
    async def _warmup_models(self):
        """Warm up AI models on startup."""
        logger.info("Warming up AI models...")
        
        try:
            # Test LLM system
            test_messages = [{"role": "user", "content": "Hi"}]
            await llm_system.generate_response(test_messages, temperature=0.1)
            
            # Test voice engines if available
            if voice_engine.stt_engines or voice_engine.tts_engines:
                logger.info("Voice engines available")
            
            self.models_warmed = True
            logger.info("Model warmup completed successfully")
            
        except (asyncio.TimeoutError, ConnectionError, RuntimeError) as e:
            logger.error(f"Model warmup failed: {e}")
            # Continue anyway with graceful degradation
    
    async def _background_maintenance(self):
        """Background maintenance tasks."""
        while True:
            try:
                # Health checks
                await llm_system.health_check()
                
                # Memory cleanup
                await concurrency_manager.semaphore.acquire()
                concurrency_manager.semaphore.release()
                
                # Log performance metrics
                metrics = perf_logger.get_metrics()
                if metrics:
                    logger.info(f"Performance metrics: {len(metrics)} tracked operations")
                
                await asyncio.sleep(300)  # 5 minutes
                
            except (asyncio.TimeoutError, RuntimeError) as e:
                logger.error(f"Background maintenance error: {e}")
                await asyncio.sleep(60)
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"✅ {self.user} is ready!")
        logger.info(SEPARATOR_LINE)
        logger.info("🎉 PRIYA - PRODUCTION GRADE SYSTEM")
        logger.info(SEPARATOR_LINE)
        logger.info("✅ Modular architecture")
        logger.info("✅ LLM fallback system")
        logger.info("✅ Voice processing")
        logger.info("✅ Concurrency control")
        logger.info("✅ Structured logging")
        logger.info("✅ Memory management")
        logger.info("✅ Timeout handling")
        logger.info("✅ Type hints & docstrings")
        logger.info(f"✅ Models warmed: {self.models_warmed}")
        logger.info(SEPARATOR_LINE)
        
        # Log system status
        llm_status = llm_system.get_status()
        voice_status = voice_engine.get_status()
        
        logger.info(f"LLM providers: {llm_status['available_providers']}/{llm_status['total_providers']}")
        logger.info(f"Voice engines: STT={len(voice_status['stt_engines'])}, TTS={len(voice_status['tts_engines'])}")
        
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=3148800&scope=bot"
        logger.info(f"🔗 Invite: {invite_url}")
    
    @commands.command()
    @with_timeout(30)
    async def join(self, ctx):
        """Join voice channel with concurrency control."""
        if not ctx.author.voice:
            await ctx.send("Join a voice channel first yaar! 🎤")
            return
        
        guild_id = ctx.guild.id
        user_id = str(ctx.author.id)
        
        # Check if already in voice
        if guild_id in self.voice_connections:
            current_user = self.voice_users.get(guild_id)
            if current_user and current_user != user_id:
                await ctx.send("I'm already in a voice channel! Use `!leave` first. 🎵")
                return
        
        try:
            async with concurrency_manager.voice_exclusive(user_id):
                # Connect to voice channel
                voice_client = await ctx.author.voice.channel.connect()
                self.voice_connections[guild_id] = voice_client
                self.voice_users[guild_id] = user_id
                
                # Check if should respond based on activity
                response_decision = priya_core.should_respond(user_id, "joined voice", True)
                
                if response_decision['should_respond']:
                    # Generate response
                    user_ctx, priya_state, activity = priya_core.get_context_for_response(user_id)
                    system_prompt = priya_core.personality_engine.build_system_prompt(
                        user_ctx, priya_state, activity
                    )
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "I joined the voice channel"}
                    ]
                    
                    response = await llm_system.generate_response(messages)
                    await ctx.send(response)
                    
                    # Update context
                    await priya_core.update_after_interaction(user_id, "joined voice", response)
                else:
                    busy_msg = response_decision.get('busy_reason', "I'm a bit busy right now")
                    await ctx.send(f"{busy_msg}, but I'll join anyway! 😊")
                
                # Start recording (simplified for production)
                logger.info(f"Voice connection established for {user_id} in guild {guild_id}")
                
        except (discord.ClientException, asyncio.TimeoutError, RuntimeError) as e:
            logger.error(f"Failed to join voice channel: {e}")
            await ctx.send(f"Couldn't join voice: {str(e)[:100]} 😅")
    
    @commands.command()
    @with_timeout(15)
    async def leave(self, ctx):
        """Leave voice channel."""
        guild_id = ctx.guild.id
        user_id = str(ctx.author.id)
        
        if guild_id not in self.voice_connections:
            await ctx.send("I'm not in a voice channel! 🤔")
            return
        
        try:
            # Generate goodbye response
            response_decision = priya_core.should_respond(user_id, "leaving voice", True)
            
            if response_decision['should_respond']:
                user_ctx, priya_state, activity = priya_core.get_context_for_response(user_id)
                system_prompt = priya_core.personality_engine.build_system_prompt(
                    user_ctx, priya_state, activity
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "I'm leaving the voice channel"}
                ]
                
                response = await llm_system.generate_response(messages)
                await ctx.send(response)
                
                await priya_core.update_after_interaction(user_id, "leaving voice", response)
            else:
                await ctx.send("Bye! Take care yaar! 👋")
            
            # Disconnect
            await self.voice_connections[guild_id].disconnect()
            del self.voice_connections[guild_id]
            self.voice_users.pop(guild_id, None)
            
            logger.info(f"Voice connection closed for guild {guild_id}")
            
        except (discord.ClientException, RuntimeError) as e:
            logger.error(f"Error leaving voice channel: {e}")
            await ctx.send(f"Error leaving voice: {str(e)[:100]} 😅")
    
    @commands.command()
    async def status(self, ctx):
        """Get bot status and health."""
        try:
            uptime = datetime.now() - self.start_time
            uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
            
            llm_status = llm_system.get_status()
            voice_status = voice_engine.get_status()
            active_requests = concurrency_manager.get_active_requests()
            
            status_msg = f"""🤖 **Priya's Status**

⏰ **Uptime:** {uptime_str}
💬 **Messages:** {self.message_count}
📝 **Responses:** {self.response_count}
🎤 **Voice Connections:** {len(self.voice_connections)}

🧠 **AI Models:** {llm_status['available_providers']}/{llm_status['total_providers']} available
🎵 **Voice Engines:** STT={len(voice_status['stt_engines'])}, TTS={len(voice_status['tts_engines'])}
⚡ **Active Requests:** {len(active_requests)}

🌟 **Models Warmed:** {'Yes' if self.models_warmed else 'No'}
"""
            
            await ctx.send(status_msg)
            
        except (KeyError, RuntimeError) as e:
            logger.error(f"Status command error: {e}")
            await ctx.send("Couldn't get status right now 😅")
    
    async def on_message(self, message):
        """Handle incoming messages."""
        if message.author == self.user:
            return
        
        # Process commands first
        await self.process_commands(message)
        
        # Skip if no guild or is command
        if not message.guild or message.content.startswith('!'):
            return
        
        self.message_count += 1
        user_id = str(message.author.id)
        
        try:
            # Check if should respond
            is_mention = self.user in message.mentions
            response_decision = priya_core.should_respond(user_id, message.content, is_mention)
            
            if not response_decision['should_respond']:
                return
            
            # Use concurrency control
            async with concurrency_manager.request_slot(user_id, "message"):
                # Get context for response (immutable copies)
                user_ctx, priya_state, activity = await priya_core.get_context_for_response(user_id)
                
                # Build system prompt
                system_prompt = priya_core.personality_engine.build_system_prompt(
                    user_ctx, priya_state, activity
                )
                
                # Get relevant history using vector search with token limits
                history = await priya_core.memory_system.get_relevant_history(
                    user_id, message.content, max_tokens=2000
                )
                
                # Add current message
                messages = [
                    {"role": "system", "content": system_prompt},
                    *history,
                    {"role": "user", "content": message.content}
                ]
                
                # Compress if needed
                messages = await context_compressor.compress_context(user_id, messages)
                
                # Show typing indicator with reduced delay
                async with message.channel.typing():
                    # Minimal realistic delay
                    delay = min(len(message.content) * 0.01, 1.5) * response_decision['delay_multiplier']
                    await asyncio.sleep(delay)
                    
                    # Generate response
                    response = await llm_system.generate_response(messages)
                    
                    if response:
                        # Add natural emojis occasionally
                        if random.random() < 0.3:
                            emojis = ['😊', '😄', '🤔', '😅', '💕', '✨', '🎉']
                            response += f" {random.choice(emojis)}"
                        
                        await message.reply(response)
                        self.response_count += 1
                        
                        # Update context
                        await priya_core.update_after_interaction(user_id, message.content, response)
                        
                        logger.info(f"Response sent to {user_id}", extra={'user_id': user_id})
        
        except (asyncio.TimeoutError, ConnectionError, RuntimeError) as e:
            logger.error(f"Message processing error: {e}", extra={'user_id': user_id})
            perf_logger.log_error(e, {'user_id': user_id, 'message_length': len(message.content)})
            
            try:
                fallback_responses = [
                    "Arre yaar, something went wrong... 😅 Try again?",
                    "Sorry, having a brain freeze moment! 🧠❄️",
                    "Oops, technical difficulties! Give me a sec 🔧"
                ]
                await message.reply(random.choice(fallback_responses))
            except discord.HTTPException:
                pass  # Don't fail on fallback
    
    async def on_error(self, event, *args, **kwargs):
        """Handle bot errors."""
        logger.error(f"Bot error in {event}: {args}")
        logger.error(traceback.format_exc())

def create_bot() -> PriyaBot:
    """Create and configure the bot instance."""
    return PriyaBot()

async def run_bot():
    """Run the bot with proper error handling."""
    bot = create_bot()
    
    try:
        await bot.start(config.discord_token)
    except (discord.LoginFailure, discord.HTTPException, ConnectionError) as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        if not bot.is_closed():
            await bot.close()

def main():
    """Main entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except (RuntimeError, OSError) as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()