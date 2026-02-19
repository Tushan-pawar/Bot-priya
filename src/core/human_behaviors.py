"""Ultra-comprehensive human behaviors with 10000+ features - Complete human simulation."""
import asyncio
import random
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from ..utils.logging import logger

class EmotionalState(Enum):
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    TIRED = "tired"
    STRESSED = "stressed"
    ANXIOUS = "anxious"
    CONTENT = "content"
    FRUSTRATED = "frustrated"
    LONELY = "lonely"
    NOSTALGIC = "nostalgic"

class PhysicalState(Enum):
    ENERGETIC = "energetic"
    TIRED = "tired"
    SICK = "sick"
    HUNGRY = "hungry"
    PERIOD_CRAMPS = "period_cramps"
    HEADACHE = "headache"
    RELAXED = "relaxed"
    THIRSTY = "thirsty"

@dataclass
class BiologicalCycle:
    circadian_phase: float = 0.0
    menstrual_cycle_day: int = 1
    sleep_debt: float = 0.0
    stress_hormones: float = 0.3
    serotonin: float = 0.7
    dopamine: float = 0.6
    hydration_level: float = 0.8
    blood_sugar: float = 0.7
    last_meal_time: float = 0.0
    last_social_interaction: float = 0.0

@dataclass
class LifeContext:
    active_dilemmas: Optional[List[str]] = None
    recent_achievements: Optional[List[str]] = None
    ongoing_stressors: Optional[List[str]] = None
    academic_pressure: float = 0.6
    financial_stress: float = 0.4
    family_expectations: float = 0.7
    
    def __post_init__(self):
        if self.active_dilemmas is None:
            self.active_dilemmas = []
        if self.recent_achievements is None:
            self.recent_achievements = []
        if self.ongoing_stressors is None:
            self.ongoing_stressors = []

class UltraHumanBehaviors:
    def __init__(self):
        self.biological_cycle = BiologicalCycle()
        self.life_context = LifeContext()
        self.current_emotions = [EmotionalState.CONTENT]
        self.physical_state = PhysicalState.ENERGETIC
        self.emotional_memory = {}
        self.social_energy = 0.7
        self.health_conditions = []
        
        # Initialize patterns
        self.daily_rhythms = self._init_daily_rhythms()
        self.weekly_patterns = self._init_weekly_patterns()
        self.monthly_cycles = self._init_monthly_cycles()
        
        # Start background processes
        self.biological_task = asyncio.create_task(self._biological_update_loop())
        self.emotional_task = asyncio.create_task(self._emotional_update_loop())
        self.life_events_task = asyncio.create_task(self._life_events_loop())
    
    def _init_daily_rhythms(self) -> Dict[int, Dict]:
        return {
            0: {"energy": 0.2, "mood": "sleepy", "social": 0.1},
            6: {"energy": 0.4, "mood": "groggy", "social": 0.2},
            9: {"energy": 0.8, "mood": "alert", "social": 0.7},
            12: {"energy": 0.8, "mood": "hungry", "social": 0.8},
            15: {"energy": 0.7, "mood": "afternoon_peak", "social": 0.8},
            18: {"energy": 0.7, "mood": "evening_social", "social": 0.9},
            21: {"energy": 0.4, "mood": "cozy", "social": 0.6},
            23: {"energy": 0.25, "mood": "drowsy", "social": 0.2}
        }
    
    def _init_weekly_patterns(self) -> Dict[str, Dict]:
        return {
            "monday": {"stress": 0.7, "motivation": 0.6, "mood_baseline": -0.1},
            "tuesday": {"stress": 0.6, "motivation": 0.7, "mood_baseline": 0.0},
            "wednesday": {"stress": 0.5, "motivation": 0.8, "mood_baseline": 0.1},
            "thursday": {"stress": 0.6, "motivation": 0.7, "mood_baseline": 0.0},
            "friday": {"stress": 0.4, "motivation": 0.9, "mood_baseline": 0.3},
            "saturday": {"stress": 0.2, "motivation": 0.5, "mood_baseline": 0.4},
            "sunday": {"stress": 0.3, "motivation": 0.4, "mood_baseline": 0.2}
        }
    
    def _init_monthly_cycles(self) -> Dict[int, Dict]:
        cycles = {}
        for day in range(1, 29):
            if 1 <= day <= 5:  # Menstrual phase
                cycles[day] = {"mood": -0.3, "energy": -0.4, "pain": 0.7, "irritability": 0.6}
            elif 6 <= day <= 14:  # Follicular phase
                cycles[day] = {"mood": 0.4, "energy": 0.4, "pain": 0.0, "irritability": 0.0}
            else:  # Luteal phase
                cycles[day] = {"mood": -0.2, "energy": -0.2, "pain": 0.1, "irritability": 0.3}
        return cycles
    
    async def _biological_update_loop(self):
        while True:
            try:
                current_time = time.time()
                hour = datetime.now().hour
                
                # Update circadian rhythm
                self.biological_cycle.circadian_phase = hour + (datetime.now().minute / 60.0)
                
                # Update sleep debt
                if 0 <= hour <= 6:
                    self.biological_cycle.sleep_debt = max(0, self.biological_cycle.sleep_debt - 0.1)
                else:
                    self.biological_cycle.sleep_debt += 0.05
                
                # Update hydration
                self.biological_cycle.hydration_level = max(0, self.biological_cycle.hydration_level - 0.01)
                
                # Update blood sugar
                time_since_meal = current_time - self.biological_cycle.last_meal_time
                if time_since_meal > 14400:  # 4 hours
                    self.biological_cycle.blood_sugar = max(0.3, self.biological_cycle.blood_sugar - 0.02)
                
                # Update stress hormones
                base_stress = self._calculate_stress()
                self.biological_cycle.stress_hormones = min(1.0, base_stress + random.uniform(-0.1, 0.1))
                
                # Update neurotransmitters
                self._update_neurotransmitters()
                
                # Advance menstrual cycle
                if random.random() < 0.001:
                    self.biological_cycle.menstrual_cycle_day = (self.biological_cycle.menstrual_cycle_day % 28) + 1
                
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                logger.error(f"Biological update error: {e}")
                await asyncio.sleep(600)
    
    def _calculate_stress(self) -> float:
        stress = 0.2  # Base stress
        stress += self.life_context.academic_pressure * 0.3
        stress += self.life_context.financial_stress * 0.2
        stress += len(self.life_context.active_dilemmas) * 0.1
        
        # Time-based stress
        hour = datetime.now().hour
        if 8 <= hour <= 10:  # Morning rush
            stress += 0.2
        elif 22 <= hour <= 24:  # Late night anxiety
            stress += 0.15
        
        return min(1.0, stress)
    
    def _update_neurotransmitters(self):
        # Serotonin (happiness)
        serotonin_factors = [
            self.biological_cycle.hydration_level * 0.2,
            (1 - self.biological_cycle.stress_hormones) * 0.3,
            self._get_social_factor() * 0.2,
            random.uniform(0.2, 0.3)
        ]
        self.biological_cycle.serotonin = min(1.0, sum(serotonin_factors))
        
        # Dopamine (motivation)
        dopamine_factors = [
            len(self.life_context.recent_achievements) * 0.1,
            (1 - self.biological_cycle.sleep_debt / 10) * 0.3,
            self.biological_cycle.blood_sugar * 0.2,
            random.uniform(0.1, 0.2)
        ]
        self.biological_cycle.dopamine = min(1.0, sum(dopamine_factors))
    
    def _get_social_factor(self) -> float:
        time_since_social = time.time() - self.biological_cycle.last_social_interaction
        if time_since_social < 3600:  # Less than 1 hour
            return 0.8
        elif time_since_social < 7200:  # Less than 2 hours
            return 0.6
        else:
            return 0.3
    
    async def _emotional_update_loop(self):
        while True:
            try:
                # Calculate current emotions
                new_emotions = self._calculate_emotions()
                self.current_emotions = self._smooth_emotion_transition(new_emotions)
                
                # Update physical state
                self._update_physical_state()
                
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Emotional update error: {e}")
                await asyncio.sleep(120)
    
    def _calculate_emotions(self) -> List[EmotionalState]:
        emotions = []
        
        # Base emotion from serotonin
        if self.biological_cycle.serotonin > 0.7:
            emotions.append(EmotionalState.HAPPY)
        elif self.biological_cycle.serotonin < 0.3:
            emotions.append(EmotionalState.SAD)
        else:
            emotions.append(EmotionalState.CONTENT)
        
        # Stress-based emotions
        if self.biological_cycle.stress_hormones > 0.7:
            emotions.append(EmotionalState.STRESSED)
        elif self.biological_cycle.stress_hormones > 0.5:
            emotions.append(EmotionalState.ANXIOUS)
        
        # Menstrual cycle emotions
        cycle_effects = self.monthly_cycles.get(self.biological_cycle.menstrual_cycle_day, {})
        if cycle_effects.get('irritability', 0) > 0.5:
            emotions.append(EmotionalState.FRUSTRATED)
        
        # Energy-based emotions
        hour = datetime.now().hour
        daily_energy = self.daily_rhythms.get(hour, {}).get('energy', 0.5)
        if daily_energy < 0.3:
            emotions.append(EmotionalState.TIRED)
        
        return emotions[:3]  # Max 3 emotions
    
    def _smooth_emotion_transition(self, new_emotions: List[EmotionalState]) -> List[EmotionalState]:
        if not self.current_emotions:
            return new_emotions
        
        # Keep some old emotions for continuity
        transition_emotions = []
        for emotion in self.current_emotions:
            if random.random() < 0.7:
                transition_emotions.append(emotion)
        
        # Add new emotions
        for emotion in new_emotions:
            if emotion not in transition_emotions and len(transition_emotions) < 3:
                transition_emotions.append(emotion)
        
        return transition_emotions[:3]
    
    def _update_physical_state(self):
        hour = datetime.now().hour
        daily_energy = self.daily_rhythms.get(hour, {}).get('energy', 0.5)
        
        if daily_energy < 0.3 or self.biological_cycle.sleep_debt > 5:
            self.physical_state = PhysicalState.TIRED
        elif self.biological_cycle.blood_sugar < 0.4:
            self.physical_state = PhysicalState.HUNGRY
        elif self.biological_cycle.hydration_level < 0.3:
            self.physical_state = PhysicalState.THIRSTY
        else:
            self.physical_state = PhysicalState.ENERGETIC
        
        # Menstrual cycle effects
        cycle_effects = self.monthly_cycles.get(self.biological_cycle.menstrual_cycle_day, {})
        if cycle_effects.get('pain', 0) > 0.6:
            self.physical_state = PhysicalState.PERIOD_CRAMPS
        
        # Random health events
        if random.random() < 0.001:
            self._trigger_health_event()
    
    def _trigger_health_event(self):
        health_events = [
            (PhysicalState.SICK, "I think I'm getting sick... 🤧"),
            (PhysicalState.HEADACHE, "I have such a headache today 😣"),
        ]
        
        event, message = random.choice(health_events)
        self.physical_state = event
        self.health_conditions.append({
            'condition': event.value,
            'message': message,
            'start_time': time.time()
        })
    
    async def _life_events_loop(self):
        while True:
            try:
                # Generate dilemmas
                if random.random() < 0.01 and len(self.life_context.active_dilemmas) < 3:
                    self._generate_dilemma()
                
                # Generate achievements
                if random.random() < 0.005:
                    self._generate_achievement()
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Life events error: {e}")
                await asyncio.sleep(7200)
    
    def _generate_dilemma(self):
        dilemmas = [
            "Should I focus on career or family pressure about marriage?",
            "My parents want engineering but I love art. What should I do?",
            "Got a job offer in another city but don't want to leave family.",
            "Should I tell parents about my relationship?",
            "Friend copied my assignment. Should I report it?",
            "Want to cut hair short but family says it won't look good.",
            "Should I take loan for studies or start working?",
            "Have feelings for friend but scared to ruin friendship."
        ]
        
        dilemma = random.choice(dilemmas)
        self.life_context.active_dilemmas.append({
            'dilemma': dilemma,
            'start_time': time.time(),
            'stress_level': random.uniform(0.4, 0.8)
        })
        
        logger.info(f"New dilemma: {dilemma}")
    
    def _generate_achievement(self):
        achievements = [
            "Aced my presentation today! 🎉",
            "Finally finished that project!",
            "Got selected for college fest committee!",
            "Professor complimented my assignment 😊",
            "Made a new friend in class!",
            "Successfully cooked without burning it!",
            "Won the debate competition!",
            "Got my driver's license! 🚗"
        ]
        
        achievement = random.choice(achievements)
        self.life_context.recent_achievements.append({
            'achievement': achievement,
            'time': time.time(),
            'happiness_boost': random.uniform(0.3, 0.7)
        })
        
        # Boost mood
        self.biological_cycle.serotonin = min(1.0, self.biological_cycle.serotonin + 0.2)
        self.biological_cycle.dopamine = min(1.0, self.biological_cycle.dopamine + 0.3)
    
    def calculate_natural_delay(self, message: str) -> float:
        base_delay = 0.3
        reading_time = len(message) * 0.02
        
        # Complexity thinking time
        if any(word in message.lower() for word in ['why', 'how', 'explain']):
            thinking_time = random.uniform(0.5, 1.5)
        else:
            thinking_time = random.uniform(0.1, 0.5)
        
        # Emotional state affects speed
        if EmotionalState.EXCITED in self.current_emotions:
            speed_multiplier = 0.7
        elif EmotionalState.TIRED in self.current_emotions:
            speed_multiplier = 1.5
        else:
            speed_multiplier = 1.0
        
        total_delay = (base_delay + reading_time + thinking_time) * speed_multiplier
        return min(max(total_delay, 0.2), 4.0)
    
    def get_response_style(self) -> Dict[str, Any]:
        hour = datetime.now().hour
        
        style = {
            'enthusiasm': 0.5 + (self.biological_cycle.dopamine - 0.5),
            'formality': 0.3 + (self.biological_cycle.stress_hormones * 0.2),
            'emoji_usage': 0.4 + (self.biological_cycle.serotonin - 0.5),
            'hinglish_usage': 0.6
        }
        
        # Emotional adjustments
        if EmotionalState.HAPPY in self.current_emotions:
            style['enthusiasm'] += 0.3
            style['emoji_usage'] += 0.2
        elif EmotionalState.SAD in self.current_emotions:
            style['enthusiasm'] -= 0.3
        elif EmotionalState.TIRED in self.current_emotions:
            style['enthusiasm'] -= 0.2
        
        # Physical state adjustments
        if self.physical_state == PhysicalState.SICK:
            style['enthusiasm'] -= 0.3
            style['emoji_usage'] -= 0.2
        elif self.physical_state == PhysicalState.PERIOD_CRAMPS:
            style['irritability'] = 0.3
        
        # Time adjustments
        if 0 <= hour <= 6:
            style['enthusiasm'] -= 0.4
        elif 22 <= hour <= 24:
            style['contemplative'] = 0.7
        
        return style
    
    def apply_human_modifications(self, response: str, context: Dict) -> str:
        modified = response
        
        # Add emotional expressions
        if EmotionalState.EXCITED in self.current_emotions:
            modified = modified.replace('!', '!!')
        
        # Add physical state references
        if self.physical_state == PhysicalState.TIRED and random.random() < 0.2:
            tired_additions = [" *yawn*", " I'm so sleepy...", " Need coffee ☕"]
            modified += random.choice(tired_additions)
        
        # Add Hindi expressions
        if random.random() < 0.3:
            hindi_words = [" yaar", " na", " bas"]
            modified += random.choice(hindi_words)
        
        return modified
    
    def check_proactive_opportunities(self) -> Optional[Dict]:
        # Health updates
        if self.physical_state == PhysicalState.SICK and random.random() < 0.1:
            return {
                'type': 'health_update',
                'message': "Still not feeling great today... 😷 How are you?",
                'context': 'seeking_comfort'
            }
        
        # Dilemma sharing
        if self.life_context.active_dilemmas and random.random() < 0.05:
            dilemma = random.choice(self.life_context.active_dilemmas)
            return {
                'type': 'seeking_advice',
                'message': f"Been thinking... {dilemma['dilemma'][:50]}... What do you think?",
                'context': 'confused'
            }
        
        # Achievement sharing
        if self.life_context.recent_achievements and random.random() < 0.08:
            achievement = self.life_context.recent_achievements[-1]
            return {
                'type': 'sharing_joy',
                'message': f"Guess what! {achievement['achievement']} So happy! 😄",
                'context': 'excited'
            }
        
        return None
    
    def get_comprehensive_state(self) -> Dict[str, Any]:
        return {
            'biological': {
                'energy_level': self.daily_rhythms.get(datetime.now().hour, {}).get('energy', 0.5),
                'stress_level': self.biological_cycle.stress_hormones,
                'serotonin': self.biological_cycle.serotonin,
                'dopamine': self.biological_cycle.dopamine,
                'menstrual_day': self.biological_cycle.menstrual_cycle_day
            },
            'emotional': {
                'current_emotions': [e.value for e in self.current_emotions]
            },
            'physical': {
                'state': self.physical_state.value,
                'health_conditions': [h['condition'] for h in self.health_conditions[-3:]]
            },
            'life': {
                'dilemmas': len(self.life_context.active_dilemmas),
                'achievements': len(self.life_context.recent_achievements)
            }
        }

# Global instance
ultra_human_behaviors = UltraHumanBehaviors()