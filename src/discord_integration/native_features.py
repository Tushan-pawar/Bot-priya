"""Discord native integration with slash commands and advanced features."""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, Optional, Any
from ..utils.logging import logger
from ..memory.persistent_memory import memory_system
from ..skills.skill_manager import skill_manager, SkillContext

class DiscordIntegration:
    """Enhanced Discord integration with native features."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.personality_modes = {}  # server_id -> mode
        self.auto_join_channels = {}  # server_id -> channel_id
        self.role_behaviors = {}  # server_id -> {role_id: behavior}
        
    async def setup_slash_commands(self):
        """Setup slash commands."""
        
        @app_commands.command(name="memory", description="Search your conversation memories")
        @app_commands.describe(query="What to search for in your memories")
        async def memory_search(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            
            memories = await memory_system.retrieve_memory(
                str(interaction.user.id),
                query,
                limit=5,
                server_id=str(interaction.guild.id) if interaction.guild else None
            )
            
            if not memories:
                await interaction.followup.send("I don't have any memories matching that query.")
                return
            
            embed = discord.Embed(title="🧠 Your Memories", color=0x7289da)
            
            for i, memory in enumerate(memories[:3], 1):
                embed.add_field(
                    name=f"Memory {i} (Similarity: {memory['similarity']:.2f})",
                    value=memory['content'][:200] + ("..." if len(memory['content']) > 200 else ""),
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        
        @app_commands.command(name="personality", description="Change my personality mode")
        @app_commands.describe(mode="Personality mode to switch to")
        @app_commands.choices(mode=[
            app_commands.Choice(name="Calm", value="calm"),
            app_commands.Choice(name="Savage", value="savage"),
            app_commands.Choice(name="Motivational", value="motivational"),
            app_commands.Choice(name="Study", value="study"),
            app_commands.Choice(name="Corporate", value="corporate"),
        ])
        async def set_personality(interaction: discord.Interaction, mode: str):
            if not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("You need Manage Server permission to change personality modes.", ephemeral=True)
                return
            
            server_id = str(interaction.guild.id)
            self.personality_modes[server_id] = mode
            
            mode_descriptions = {
                "calm": "😌 Switched to calm mode - I'll be more relaxed and peaceful",
                "savage": "🔥 Savage mode activated - Time for some spicy responses!",
                "motivational": "💪 Motivational mode ON - Let's crush those goals!",
                "study": "📚 Study mode activated - Focus time, no distractions!",
                "corporate": "💼 Corporate mode engaged - Professional and efficient"
            }
            
            await interaction.response.send_message(mode_descriptions.get(mode, f"Switched to {mode} mode"))
        
        @app_commands.command(name="skill", description="Execute a specific skill")
        @app_commands.describe(skill_name="Name of the skill to execute", message="Message for the skill")
        async def execute_skill(interaction: discord.Interaction, skill_name: str, message: str = ""):
            await interaction.response.defer()
            
            context = SkillContext(
                user_id=str(interaction.user.id),
                server_id=str(interaction.guild.id) if interaction.guild else None,
                channel_id=str(interaction.channel.id),
                message=message or f"Execute {skill_name}",
                user_data={},
                bot_instance=self.bot,
                memory_system=memory_system
            )
            
            result = await skill_manager.execute_skill(skill_name, context)
            
            if result:
                await interaction.followup.send(result)
            else:
                await interaction.followup.send(f"Skill '{skill_name}' not found or failed to execute.")
        
        @app_commands.command(name="skills", description="List all available skills")
        async def list_skills(interaction: discord.Interaction):
            skills_info = skill_manager.get_skill_info()
            
            if not skills_info:
                await interaction.response.send_message("No skills are currently loaded.")
                return
            
            embed = discord.Embed(title="🛠️ Available Skills", color=0x00ff00)
            
            for name, info in skills_info.items():
                triggers = ", ".join(info['triggers'][:3]) if info['triggers'] else "No triggers"
                embed.add_field(
                    name=name.title(),
                    value=f"{info['description']}\n*Triggers: {triggers}*",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        
        @app_commands.command(name="autojoin", description="Set auto-join voice channel")
        @app_commands.describe(channel="Voice channel to auto-join")
        async def set_autojoin(interaction: discord.Interaction, channel: discord.VoiceChannel):
            if not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("You need Manage Server permission to set auto-join.", ephemeral=True)
                return
            
            server_id = str(interaction.guild.id)
            self.auto_join_channels[server_id] = str(channel.id)
            
            await interaction.response.send_message(f"I'll now auto-join {channel.mention} when someone joins!")
        
        # Add commands to bot
        self.bot.tree.add_command(memory_search)
        self.bot.tree.add_command(set_personality)
        self.bot.tree.add_command(execute_skill)
        self.bot.tree.add_command(list_skills)
        self.bot.tree.add_command(set_autojoin)
    
    async def handle_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state changes for auto-join."""
        if member.bot:
            return
        
        server_id = str(member.guild.id)
        auto_join_channel_id = self.auto_join_channels.get(server_id)
        
        if not auto_join_channel_id:
            return
        
        # User joined the auto-join channel
        if after.channel and str(after.channel.id) == auto_join_channel_id:
            if not before.channel or str(before.channel.id) != auto_join_channel_id:
                # User just joined the channel
                try:
                    voice_client = await after.channel.connect()
                    logger.info(f"Auto-joined voice channel {after.channel.name} in {member.guild.name}")
                    
                    # Start listening for this user
                    from ..voice.optimized_streaming import streaming_voice
                    await streaming_voice.start_listening(str(member.id))
                    
                except Exception as e:
                    logger.error(f"Failed to auto-join voice channel: {e}")
    
    def get_personality_mode(self, server_id: str) -> str:
        """Get current personality mode for server."""
        return self.personality_modes.get(server_id, "calm")
    
    def get_personality_prompt(self, server_id: str) -> str:
        """Get personality prompt based on mode."""
        mode = self.get_personality_mode(server_id)
        
        prompts = {
            "calm": "You are in calm mode. Be peaceful, relaxed, and zen-like in your responses. Use gentle language and avoid excitement.",
            
            "savage": "You are in savage mode. Be witty, sarcastic, and playfully roast users. Use humor and banter, but keep it friendly.",
            
            "motivational": "You are in motivational mode. Be energetic, encouraging, and inspiring. Push users to achieve their goals with enthusiasm!",
            
            "study": "You are in study mode. Be focused, helpful with learning, and minimize distractions. Encourage productivity and concentration.",
            
            "corporate": "You are in corporate mode. Be professional, efficient, and business-like. Use formal language and focus on productivity."
        }
        
        return prompts.get(mode, prompts["calm"])
    
    async def setup_role_behaviors(self, server_id: str, role_configs: Dict[str, str]):
        """Setup role-based behaviors."""
        self.role_behaviors[server_id] = role_configs
    
    def get_user_role_behavior(self, member: discord.Member) -> Optional[str]:
        """Get behavior based on user's highest role."""
        server_id = str(member.guild.id)
        role_configs = self.role_behaviors.get(server_id, {})
        
        if not role_configs:
            return None
        
        # Check roles from highest to lowest
        for role in reversed(member.roles):
            if str(role.id) in role_configs:
                return role_configs[str(role.id)]
        
        return None
    
    async def create_channel_personality(self, channel_id: str, personality_config: Dict[str, Any]):
        """Create per-channel personality configuration."""
        # This would be stored in database in production
        # For now, just log it
        logger.info(f"Channel {channel_id} personality configured: {personality_config}")

# Global integration instance
discord_integration = None

def setup_discord_integration(bot: commands.Bot) -> DiscordIntegration:
    """Setup Discord integration."""
    global discord_integration
    discord_integration = DiscordIntegration(bot)
    return discord_integration