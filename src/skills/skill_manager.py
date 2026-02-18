"""Dynamic skill loading and execution system."""
import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from ..utils.logging import logger

@dataclass
class SkillContext:
    """Context passed to skills."""
    user_id: str
    server_id: Optional[str]
    channel_id: str
    message: str
    user_data: Dict[str, Any]
    bot_instance: Any
    memory_system: Any

class BaseSkill(ABC):
    """Base class for all skills."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Skill name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Skill description."""
        pass
    
    @property
    def triggers(self) -> List[str]:
        """Keywords that trigger this skill."""
        return []
    
    @property
    def requires_memory(self) -> bool:
        """Whether skill needs memory access."""
        return False
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> str:
        """Execute the skill."""
        pass
    
    def should_trigger(self, message: str) -> bool:
        """Check if skill should be triggered."""
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in self.triggers)

class SkillManager:
    """Manages dynamic skill loading and execution."""
    
    def __init__(self, skills_dir: str = "src/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, BaseSkill] = {}
        self.skill_modules = {}
        
    async def load_skills(self) -> None:
        """Dynamically load all skills."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True)
            logger.info(f"Created skills directory: {self.skills_dir}")
            return
        
        # Find all Python files in skills directory
        skill_files = list(self.skills_dir.glob("*.py"))
        
        for skill_file in skill_files:
            if skill_file.name.startswith("__"):
                continue
            
            try:
                await self._load_skill_file(skill_file)
            except Exception as e:
                logger.error(f"Failed to load skill {skill_file.name}: {e}")
        
        logger.info(f"Loaded {len(self.skills)} skills: {list(self.skills.keys())}")
    
    async def _load_skill_file(self, skill_file: Path) -> None:
        """Load a single skill file."""
        module_name = f"skills.{skill_file.stem}"
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, skill_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find skill classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseSkill) and 
                    obj != BaseSkill):
                    
                    skill_instance = obj()
                    self.skills[skill_instance.name] = skill_instance
                    self.skill_modules[skill_instance.name] = module
                    
                    logger.info(f"Loaded skill: {skill_instance.name}")
                    
        except Exception as e:
            logger.error(f"Error loading skill file {skill_file}: {e}")
    
    async def reload_skill(self, skill_name: str) -> bool:
        """Reload a specific skill."""
        if skill_name not in self.skill_modules:
            return False
        
        try:
            module = self.skill_modules[skill_name]
            importlib.reload(module)
            
            # Re-instantiate skill
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseSkill) and 
                    obj != BaseSkill):
                    
                    skill_instance = obj()
                    if skill_instance.name == skill_name:
                        self.skills[skill_name] = skill_instance
                        logger.info(f"Reloaded skill: {skill_name}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to reload skill {skill_name}: {e}")
            return False
    
    async def execute_skill(self, skill_name: str, context: SkillContext) -> Optional[str]:
        """Execute a specific skill."""
        if skill_name not in self.skills:
            return None
        
        skill = self.skills[skill_name]
        
        try:
            result = await skill.execute(context)
            logger.info(f"Executed skill {skill_name} for user {context.user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Skill {skill_name} execution failed: {e}")
            return f"Sorry, the {skill_name} skill encountered an error."
    
    async def find_matching_skills(self, message: str) -> List[str]:
        """Find skills that match the message."""
        matching_skills = []
        
        for skill_name, skill in self.skills.items():
            if skill.should_trigger(message):
                matching_skills.append(skill_name)
        
        return matching_skills
    
    def get_skill_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all loaded skills."""
        return {
            name: {
                'description': skill.description,
                'triggers': skill.triggers,
                'requires_memory': skill.requires_memory
            }
            for name, skill in self.skills.items()
        }
    
    async def auto_execute(self, context: SkillContext) -> Optional[str]:
        """Automatically execute matching skills."""
        matching_skills = await self.find_matching_skills(context.message)
        
        if not matching_skills:
            return None
        
        # Execute first matching skill
        skill_name = matching_skills[0]
        return await self.execute_skill(skill_name, context)

# Global skill manager
skill_manager = SkillManager()