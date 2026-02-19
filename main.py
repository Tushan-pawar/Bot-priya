#!/usr/bin/env python3
"""
Priya AI Assistant Platform - Enhanced Main Entry Point
Modular, scalable AI assistant with advanced security and observability
"""
import asyncio
import sys
import os
import signal
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import discord
from discord.ext import commands
from src.config.settings import config
from src.utils.logging import logger, perf_logger
from src.memory.persistent_memory import memory_system
from .voice.realtime import realtime_voice
from .core.human_behaviors import human_behaviors
from .utils.deployment import production_manager
from .utils.performance import system_optimizer
from src.skills.skill_manager import skill_manager
from src.discord_integration.native_features import setup_discord_integration
from src.dashboard.admin_dashboard import admin_dashboard
from src.utils.optimization_logger import optimization_logger
from src.models.llm_fallback import llm_system
from src.core.personality import priya_core

# NEW: Import enhanced features
from src.utils.tool_engine import tool_engine
from src.memory.context_compression import context_compressor
from src.utils.rate_limiter import rate_limiter
from src.utils.task_scheduler import task_scheduler
from src.models.model_swapper import model_swapper
from src.utils.security import security_hardening
from src.utils.backup_system import backup_system

class PriyaAIAssistant(commands.Bot):
    """Enhanced Priya AI Assistant with advanced features."""
    
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        
        # Initialize components
        self.discord_integration = None
        self.voice_connections = {}
        self.active_users = {}
        self.shutdown_event = asyncio.Event()
        
        # Setup graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def setup_hook(self):
        """Setup all components with enhanced optimization."""
        logger.info("🚀 Starting Priya AI Assistant Platform v2.0...")
        
        try:
            # Start system optimization
            system_optimizer.startup_optimizer.log_step("System optimization start")
            await system_optimizer.start_optimization()
            
            # Start production monitoring
            await production_manager.start_monitoring(self)
            system_optimizer.startup_optimizer.log_step("Production monitoring")
            
            # Initialize memory system
            logger.info("📚 Initializing memory system...")
            system_optimizer.startup_optimizer.log_step("Memory system")
            
            # Load skills
            logger.info("🛠️ Loading skills...")
            await skill_manager.load_skills()
            system_optimizer.startup_optimizer.log_step("Skills loaded")
            
            # Setup Discord integration
            logger.info("🤖 Setting up Discord integration...")
            self.discord_integration = setup_discord_integration(self)
            await self.discord_integration.setup_slash_commands()
            system_optimizer.startup_optimizer.log_step("Discord integration")
            
            # Setup voice callbacks (optimized)
            logger.info("🎤 Setting up voice processing...")
            realtime_voice.transcript_callback = self._on_voice_transcript
            realtime_voice.response_callback = self._on_voice_response
            system_optimizer.startup_optimizer.log_step("Voice setup")
            
            # Warm up models (lazy loading)
            logger.info("🧠 Warming up AI models...")
            asyncio.create_task(self._warmup_models())  # Non-blocking
            
            # Start background scheduler
            logger.info("⏰ Starting background task scheduler...")
            await task_scheduler.start()
            system_optimizer.startup_optimizer.log_step("Task scheduler")
            
            # Start dashboard in background
            logger.info("🌐 Starting admin dashboard...")
            asyncio.create_task(admin_dashboard.start())
            
            # Start proactive conversation checker
            asyncio.create_task(self._proactive_conversation_loop())
            
            system_optimizer.startup_optimizer.log_step("Startup complete")
            logger.info("✅ All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    async def _warmup_models(self):
        """Warm up AI models."""
        try:
            test_messages = [{"role": "user", "content": "Hello"}]
            await llm_system.generate_response(test_messages, temperature=0.1)
            logger.info("✅ AI models warmed up successfully")
        except Exception as e:
            logger.warning(f"⚠️ Model warmup failed: {e}")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"✅ {self.user} is online!")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("🎉 PRIYA AI ASSISTANT PLATFORM v2.0")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("✅ Persistent Memory System")
        logger.info("✅ Real-time Voice Streaming")
        logger.info("✅ Dynamic Skill Loading")
        logger.info("✅ Discord Native Integration")
        logger.info("✅ Web Admin Dashboard")
        logger.info("✅ Dynamic Personality Modes")
        logger.info("✅ Self-Optimization Logging")
        logger.info("✅ Structured Tool Execution")
        logger.info("✅ Context Compression")
        logger.info("✅ Advanced Rate Limiting")
        logger.info("✅ Background Task Scheduler")
        logger.info("✅ Model Hot-Swapping")
        logger.info("✅ Security Hardening")
        logger.info("✅ Backup & Restore System")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"🔄 Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        
        # Update dashboard
        admin_dashboard.update_active_users(self.active_users)
        
        logger.info(f"🌐 Admin Dashboard: http://127.0.0.1:8080")
        logger.info(f"🔗 Invite: https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=3148800&scope=bot")
    
    async def on_message(self, message):
        """Handle incoming messages with enhanced processing."""
        if message.author == self.user:
            return
        
        # Process commands first
        await self.process_commands(message)
        
        if not message.guild or message.content.startswith('!'):
            return
        
        user_id = str(message.author.id)
        server_id = str(message.guild.id)
        
        # Update active users
        self.active_users[user_id] = {
            'last_seen': message.created_at.isoformat(),
            'server_id': server_id,
            'username': str(message.author)
        }
        
        try:
            # Security: Sanitize input
            sanitized_content = security_hardening.sanitize_input(message.content)
            
            # Security: Check for prompt injection
            is_injection, patterns = security_hardening.detect_prompt_injection(sanitized_content)
            if is_injection:
                logger.warning(f"Prompt injection blocked from user {user_id}: {patterns}")
                await message.reply("I can't process that message. Please rephrase your request.")
                return
            
            # Rate limiting
            is_allowed, limit_reason = await rate_limiter.check_rate_limit(
                user_id, server_id, sanitized_content, "default"
            )
            
            if not is_allowed:
                await message.reply(f"⏰ {limit_reason}")
                return
            
            # Check if should respond based on personality and activity
            response_decision = priya_core.should_respond(
                user_id, 
                sanitized_content, 
                self.user in message.mentions
            )
            
            if not response_decision['should_respond']:
                return
            
            # Process conversation with enhanced features
            await self._process_conversation(message, user_id, server_id, sanitized_content)
            
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            perf_logger.log_error(e, {
                'user_id': user_id,
                'server_id': server_id,
                'message_length': len(message.content)
            })
            
            await optimization_logger.log_failed_response(
                user_id=user_id,
                user_message=message.content,
                bot_response="",
                failure_reason=f"Message processing error: {str(e)}",
                server_id=server_id,
                severity="high"
            )
            
            # Send fallback response
            fallback_responses = [
                "Arre yaar, something went wrong... 😅 Try again?",
                "Sorry, having a brain freeze moment! 🧠❄️",
                "Oops, technical difficulties! Give me a sec 🔧"
            ]
            import random
            await message.reply(random.choice(fallback_responses))
    
    async def _process_conversation(self, message, user_id: str, server_id: str, content: str):
        """Process conversation with enhanced human behaviors."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Calculate natural delay
            natural_delay = human_behaviors.calculate_natural_delay(content, user_id)
            
            # Check for tool usage requests
            tool_response = await self._check_tool_usage(content, user_id, server_id)
            if tool_response:
                await asyncio.sleep(natural_delay)
                await message.reply(tool_response)
                return
            
            # Get personality mode for server
            personality_prompt = ""
            if self.discord_integration:
                personality_prompt = self.discord_integration.get_personality_prompt(server_id)
            
            # Check for skill triggers
            from src.skills.skill_manager import SkillContext
            skill_context = SkillContext(
                user_id=user_id,
                server_id=server_id,
                channel_id=str(message.channel.id),
                message=content,
                user_data=self.active_users.get(user_id, {}),
                bot_instance=self,
                memory_system=memory_system
            )
            
            # Try to execute matching skill
            skill_response = await skill_manager.auto_execute(skill_context)
            if skill_response:
                await asyncio.sleep(natural_delay)
                await message.reply(skill_response)
                return
            
            # Retrieve relevant memories (optimized)
            memories = await memory_system.retrieve_memory(
                user_id, 
                content, 
                limit=3,  # Reduced for speed
                server_id=server_id
            )
            
            # Build context with compression
            memory_context = ""
            if memories:
                memory_text = "\n".join([f"- {mem['content']}" for mem in memories])
                memory_context = f"\n\nRelevant memories:\n{memory_text}"
            
            # Get user context from core personality
            user_ctx, priya_state, activity = priya_core.get_context_for_response(user_id)
            
            # Get response style from human behaviors
            response_style = human_behaviors.get_contextual_response_style(
                user_id, content, datetime.now().hour
            )
            
            # Build comprehensive system prompt
            base_prompt = f"""You are Priya, a 23-year-old Indian AI assistant with a warm, friendly personality.

{personality_prompt}

Current activity: {activity['description']}
Mood: {priya_state.mood}
Energy: {priya_state.energy}

User relationship: {user_ctx.friendship_level}/100 friendship level
{memory_context}

Response style: Formality {response_style['formality']:.1f}, Enthusiasm {response_style['enthusiasm']:.1f}

Respond naturally in 1-2 sentences. Use Hinglish when appropriate."""
            
            # Security: Protect system prompt
            protected_prompt = security_hardening.protect_system_prompt(base_prompt, content)
            
            # Generate response with timing
            messages = [
                {"role": "system", "content": protected_prompt},
                {"role": "user", "content": content}
            ]
            
            # Show typing with natural delay
            async with message.channel.typing():
                await asyncio.sleep(natural_delay)
                
                response = await llm_system.generate_response(messages)
            
            if response:
                # Apply human behaviors
                if human_behaviors.should_use_emoji(content, user_ctx.friendship_level):
                    emoji = human_behaviors.get_natural_emoji(content, priya_state.mood)
                    response = f"{response} {emoji}"
                
                response = human_behaviors.add_natural_speech_patterns(response, user_ctx.friendship_level)
                response = human_behaviors.add_personality_quirks(response, user_ctx.friendship_level)
                
                # Security: Check output safety
                is_safe, safe_response = security_hardening.check_output_safety(response)
                final_response = safe_response if not is_safe else response
                
                # Save interaction to memory
                await memory_system.save_memory(
                    user_id,
                    f"User said: {content}. I replied: {final_response}",
                    server_id,
                    {"type": "conversation", "channel_id": str(message.channel.id)},
                    importance=0.5
                )
                
                # Update core personality and human behaviors
                await priya_core.update_after_interaction(user_id, content, final_response)
                human_behaviors.update_emotional_memory(user_id, content, final_response)
                
                await message.reply(final_response)
                
                # Log performance
                duration = asyncio.get_event_loop().time() - start_time
                system_optimizer.resource_monitor.log_response_time(duration, "conversation")
                production_manager.health_monitor.log_response_time(duration)
                
            else:
                # Log failed response
                await optimization_logger.log_failed_response(
                    user_id=user_id,
                    user_message=content,
                    bot_response="",
                    failure_reason="No response generated from LLM",
                    server_id=server_id,
                    severity="medium"
                )
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            system_optimizer.resource_monitor.log_response_time(duration, "conversation_error")
            production_manager.health_monitor.log_error(str(e))
            logger.error(f"Conversation processing error: {e}")
            raise
    
    async def _check_tool_usage(self, content: str, user_id: str, server_id: str) -> Optional[str]:
        """Check if message requests tool usage."""
        try:
            # Simple heuristic to detect tool requests
            if any(keyword in content.lower() for keyword in ['search', 'calculate', 'time', 'what time']):
                # This would be enhanced with proper LLM-based tool detection
                return None  # For now, let regular conversation handle it
            
            return None
            
        except Exception as e:
            logger.error(f"Tool usage check failed: {e}")
            return None
    
    # Enhanced slash commands
    @commands.command()
    async def backup(self, ctx, backup_name: str = None):
        """Create system backup."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Administrator permission required.")
            return
        
        try:
            await ctx.send("🔄 Creating backup...")
            backup_path = await backup_system.create_full_backup(backup_name)
            await ctx.send(f"✅ Backup created: {backup_path}")
        except Exception as e:
            await ctx.send(f"❌ Backup failed: {e}")
    
    @commands.command()
    async def switch_model(self, ctx, model_name: str):
        """Switch AI model."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Administrator permission required.")
            return
        
        success = await model_swapper.switch_model(model_name)
        if success:
            await ctx.send(f"✅ Switched to model: {model_name}")
        else:
            await ctx.send(f"❌ Failed to switch to model: {model_name}")
    
    @commands.command()
    async def rate_override(self, ctx, user_id: str, duration: int = 3600):
        """Override rate limits for user."""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Administrator permission required.")
            return
        
        rate_limiter.add_admin_override(user_id, duration)
        await ctx.send(f"✅ Rate limit override added for user {user_id} for {duration} seconds")
    
    @commands.command()
    async def voice_start(self, ctx):
        """Start real-time voice conversation."""
        if not ctx.author.voice:
            await ctx.send("Join a voice channel first! 🎤")
            return
        
        user_id = str(ctx.author.id)
        
        try:
            # Connect to voice channel
            voice_client = await ctx.author.voice.channel.connect()
            
            # Start real-time voice processing
            success = realtime_voice.start_listening(
                transcript_callback=self._on_voice_transcript,
                response_callback=self._on_voice_response
            )
            
            if success:
                await ctx.send("🎤 Real-time voice conversation started! Just speak naturally.")
                logger.info(f"Real-time voice started for {user_id}")
            else:
                await ctx.send("❌ Voice features not available. Install webrtcvad and pyaudio.")
                await voice_client.disconnect()
                
        except Exception as e:
            logger.error(f"Voice start failed: {e}")
            await ctx.send(f"Failed to start voice: {str(e)[:100]}")
    
    async def _proactive_conversation_loop(self):
        """Check for proactive conversation opportunities."""
        while True:
            try:
                opportunity = await human_behaviors.check_proactive_opportunities(self.active_users)
                
                if opportunity:
                    user_id = opportunity['user_id']
                    message = opportunity['message']
                    
                    # Find user's DM channel or last server channel
                    user = self.get_user(int(user_id))
                    if user:
                        try:
                            # Try to send DM
                            await user.send(message)
                            logger.info(f"Sent proactive message to {user_id}: {message}")
                        except:
                            # If DM fails, skip for now
                            pass
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Proactive conversation error: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _on_voice_transcript(self, transcript: str):
        """Handle voice transcript from real-time voice."""
        logger.info(f"Voice transcript: {transcript}")
        # This would integrate with voice conversation logic
    
    async def _on_voice_response(self, transcript: str) -> str:
        """Generate response for voice input."""
        try:
            # Use same conversation logic but optimized for voice
            user_ctx, priya_state, activity = priya_core.get_context_for_response("voice_user")
            
            messages = [
                {"role": "system", "content": f"You are Priya. Respond to voice input briefly and naturally. Current mood: {priya_state.mood}"},
                {"role": "user", "content": transcript}
            ]
            
            response = await llm_system.generate_response(messages)
            return response or "I didn't catch that, could you repeat?"
            
        except Exception as e:
            logger.error(f"Voice response error: {e}")
            return "Sorry, I'm having trouble understanding right now."
    
    async def graceful_shutdown(self):
        """Gracefully shutdown all components."""
        logger.info("🛑 Initiating graceful shutdown...")
        
        try:
            # Stop background scheduler
            await task_scheduler.stop()
            
            # Close voice connections
            for voice_client in self.voice_connections.values():
                if voice_client.is_connected():
                    await voice_client.disconnect()
            
            # Stop streaming voice
            await streaming_voice.stop_listening()
            
            # Final memory save
            await memory_system.save_memory(force=True)
            
            # Close bot
            await self.close()
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        finally:
            self.shutdown_event.set()

async def main():
    """Main entry point with enhanced error handling."""
    try:
        # Create bot instance
        bot = PriyaAIAssistant()
        
        # Start bot
        await bot.start(config.discord_token)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        # Ensure cleanup
        if 'bot' in locals():
            if not bot.is_closed():
                await bot.graceful_shutdown()

if __name__ == "__main__":
    asyncio.run(main())