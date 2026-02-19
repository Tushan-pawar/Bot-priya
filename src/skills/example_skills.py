"""Example skills for the AI assistant."""
import asyncio
from typing import List
from .skill_manager import BaseSkill, SkillContext

class SummarizeSkill(BaseSkill):
    """Summarize text or conversation history."""
    
    @property
    def name(self) -> str:
        return "summarize"
    
    @property
    def description(self) -> str:
        return "Summarize text, conversations, or topics"
    
    @property
    def triggers(self) -> List[str]:
        return ["summarize", "summary", "tldr", "brief"]
    
    @property
    def requires_memory(self) -> bool:
        return True
    
    async def execute(self, context: SkillContext) -> str:
        # Get recent memories for context
        memories = await context.memory_system.retrieve_memory(
            context.user_id, 
            context.message, 
            limit=10
        )
        
        if not memories:
            return "I don't have enough context to summarize. Let's chat more first!"
        
        # Create summary prompt
        memory_text = "\n".join([m['content'] for m in memories])
        summary_prompt = f"""
        Based on our conversation history, provide a brief summary:
        
        {memory_text}
        
        Current request: {context.message}
        
        Provide a concise summary in 2-3 sentences.
        """
        
        # Use LLM to generate summary
        from ..models.llm_fallback import llm_system
        messages = [{"role": "user", "content": summary_prompt}]
        
        summary = await llm_system.generate_response(messages)
        return f"📝 **Summary**: {summary}"

class CodeReviewSkill(BaseSkill):
    """Review code snippets."""
    
    @property
    def name(self) -> str:
        return "code_review"
    
    @property
    def description(self) -> str:
        return "Review and analyze code snippets"
    
    @property
    def triggers(self) -> List[str]:
        return ["review code", "code review", "check code", "```"]
    
    async def execute(self, context: SkillContext) -> str:
        # Extract code from message
        message = context.message
        
        if "```" in message:
            # Extract code block
            parts = message.split("```")
            if len(parts) >= 3:
                code = parts[1]
                if code.startswith(('python', 'js', 'java', 'cpp')):
                    code = '\n'.join(code.split('\n')[1:])
            else:
                code = message
        else:
            code = message
        
        review_prompt = f"""
        Review this code and provide feedback on:
        1. Code quality and best practices
        2. Potential bugs or issues
        3. Performance improvements
        4. Security concerns
        
        Code:
        ```
        {code}
        ```
        
        Provide constructive feedback in a friendly tone.
        """
        
        from ..models.llm_fallback import llm_system
        messages = [{"role": "user", "content": review_prompt}]
        
        review = await llm_system.generate_response(messages)
        return f"🔍 **Code Review**:\n{review}"

class StudyModeSkill(BaseSkill):
    """Study mode with focus techniques."""
    
    @property
    def name(self) -> str:
        return "study_mode"
    
    @property
    def description(self) -> str:
        return "Activate study mode with focus techniques and reminders"
    
    @property
    def triggers(self) -> List[str]:
        return ["study mode", "focus", "study session", "pomodoro"]
    
    async def execute(self, context: SkillContext) -> str:
        # Save study session start
        await context.memory_system.save_memory(
            context.user_id,
            f"Started study session: {context.message}",
            context.server_id,
            {"type": "study_session", "action": "start"},
            importance=0.8
        )
        
        return """📚 **Study Mode Activated!**

🎯 **Focus Tips:**
• Remove distractions (phone, social media)
• Set specific goals for this session
• Take breaks every 25-30 minutes
• Stay hydrated!

⏰ **Pomodoro Technique:**
25 min work → 5 min break → repeat

I'll check on you in 25 minutes! Type `!break` when you need a break.
Good luck yaar! You've got this! 💪"""

class RoastSkill(BaseSkill):
    """Playful roasting skill."""
    
    @property
    def name(self) -> str:
        return "roast"
    
    @property
    def description(self) -> str:
        return "Playful roasting and banter"
    
    @property
    def triggers(self) -> List[str]:
        return ["roast me", "insult me", "be mean", "savage mode"]
    
    async def execute(self, context: SkillContext) -> str:
        roasts = [
            "Arre yaar, you want me to roast you? Your WiFi connection already does that every day! 😂",
            "I would roast you, but I don't want to hurt your feelings... oh wait, you asked for it! 🔥",
            "You're like a software update - nobody wants you, but you keep showing up anyway! 😅",
            "I'd make fun of your coding skills, but I don't punch down that far! 💻",
            "You're so slow, even Internet Explorer feels bad for you! 🐌"
        ]
        
        import random
        return random.choice(roasts)

class FocusTimerSkill(BaseSkill):
    """Focus timer with reminders."""
    
    @property
    def name(self) -> str:
        return "focus_timer"
    
    @property
    def description(self) -> str:
        return "Set focus timers with reminders"
    
    @property
    def triggers(self) -> List[str]:
        return ["timer", "remind me", "focus timer", "set timer"]
    
    async def execute(self, context: SkillContext) -> str:
        # Extract time from message
        import re
        time_match = re.search(r'(\d+)\s*(min|minute|hour|hr)', context.message.lower())
        
        if time_match:
            duration = int(time_match.group(1))
            unit = time_match.group(2)
            
            if unit in ['hour', 'hr']:
                seconds = duration * 3600
                time_str = f"{duration} hour{'s' if duration > 1 else ''}"
            else:
                seconds = duration * 60
                time_str = f"{duration} minute{'s' if duration > 1 else ''}"
            
            # Start timer - save task to prevent garbage collection
            self._timer_task = asyncio.create_task(self._timer_reminder(context, seconds, time_str))
            
            return f"⏰ Timer set for {time_str}! I'll remind you when it's done. Stay focused! 💪"
        
        return "⏰ Please specify a time! Example: 'Set timer for 25 minutes' or 'Timer 1 hour'"
    
    async def _timer_reminder(self, context: SkillContext, seconds: int, time_str: str):
        """Send reminder after timer expires."""
        await asyncio.sleep(seconds)
        
        # In production, this would send a message to the user
        # For now, just log it
        from ..utils.logging import logger
        logger.info(f"Timer expired for user {context.user_id}: {time_str}")
        
        # Save reminder to memory
        await context.memory_system.save_memory(
            context.user_id,
            f"Focus timer completed: {time_str}",
            context.server_id,
            {"type": "timer", "duration": time_str},
            importance=0.6
        )