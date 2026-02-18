"""
DYNAMIC SELF-LEARNING TRACKER SYSTEM
Priya autonomously creates, manages, and learns from her own tracking system
She decides what to track, what categories to create, and how to score people
"""

import json
import os
from datetime import datetime

class DynamicTrackerSystem:
    def __init__(self):
        self.tracker_file = "priya_dynamic_tracker.json"
        self.tracker = self.load_tracker()
    
    def load_tracker(self):
        """Load Priya's self-created tracker"""
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return {
            'people': {},  # People she tracks
            'categories': {},  # Categories she created
            'observations': [],  # Her observations
            'patterns': {},  # Patterns she discovered
            'insights': [],  # Her insights
            'rules': [],  # Rules she created
            'predictions': {},  # Her predictions
            'experiments': [],  # Social experiments she's running
            'hypotheses': [],  # Her theories about people
            'learnings': [],  # What she learned
            'meta': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_observations': 0,
                'total_insights': 0
            }
        }
    
    def save_tracker(self):
        """Save tracker to file"""
        self.tracker['meta']['last_updated'] = datetime.now().isoformat()
        with open(self.tracker_file, 'w') as f:
            json.dump(self.tracker, f, indent=2)
    
    def add_person(self, user_id, initial_traits=None):
        """Priya adds a person to her tracker"""
        if user_id not in self.tracker['people']:
            self.tracker['people'][user_id] = {
                'added_date': datetime.now().isoformat(),
                'traits': initial_traits or {},
                'scores': {},  # Dynamic scoring system
                'observations': [],
                'patterns': [],
                'predictions': [],
                'relationship_type': 'unknown',
                'trust_level': 0,
                'compatibility': 0,
                'energy_match': 0,
                'humor_compatibility': 0,
                'emotional_intelligence': 0,
                'conversation_quality': 0,
                'reliability': 0,
                'authenticity': 0,
                'growth_potential': 0,
                'red_flags': [],
                'green_flags': [],
                'yellow_flags': [],
                'strengths': [],
                'weaknesses': [],
                'quirks': [],
                'triggers': [],
                'motivations': [],
                'fears': [],
                'values': [],
                'communication_style': '',
                'attachment_style': '',
                'personality_type': '',
                'love_language': '',
                'conflict_style': '',
                'notes': []
            }
            self.save_tracker()
    
    def create_category(self, category_name, description, scoring_method):
        """Priya creates a new tracking category"""
        if category_name not in self.tracker['categories']:
            self.tracker['categories'][category_name] = {
                'created': datetime.now().isoformat(),
                'description': description,
                'scoring_method': scoring_method,
                'min_score': 0,
                'max_score': 100,
                'tracked_people': [],
                'insights': []
            }
            self.save_tracker()
    
    def add_observation(self, user_id, observation, category=None):
        """Priya records an observation"""
        obs = {
            'date': datetime.now().isoformat(),
            'observation': observation,
            'category': category,
            'importance': self.calculate_importance(observation)
        }
        
        self.tracker['observations'].append(obs)
        
        if user_id in self.tracker['people']:
            self.tracker['people'][user_id]['observations'].append(obs)
        
        self.tracker['meta']['total_observations'] += 1
        self.save_tracker()
    
    def update_score(self, user_id, category, score, reason):
        """Priya updates a person's score in a category"""
        if user_id in self.tracker['people']:
            if category not in self.tracker['people'][user_id]['scores']:
                self.tracker['people'][user_id]['scores'][category] = []
            
            self.tracker['people'][user_id]['scores'][category].append({
                'date': datetime.now().isoformat(),
                'score': score,
                'reason': reason
            })
            self.save_tracker()
    
    def add_trait(self, user_id, trait_name, trait_value, confidence=0.5):
        """Priya adds/updates a trait for someone"""
        if user_id in self.tracker['people']:
            self.tracker['people'][user_id]['traits'][trait_name] = {
                'value': trait_value,
                'confidence': confidence,
                'last_updated': datetime.now().isoformat()
            }
            self.save_tracker()
    
    def remove_trait(self, user_id, trait_name):
        """Priya removes a trait"""
        if user_id in self.tracker['people']:
            if trait_name in self.tracker['people'][user_id]['traits']:
                del self.tracker['people'][user_id]['traits'][trait_name]
                self.save_tracker()
    
    def add_pattern(self, pattern_description, affected_people, confidence):
        """Priya discovers a pattern"""
        pattern = {
            'date': datetime.now().isoformat(),
            'description': pattern_description,
            'affected_people': affected_people,
            'confidence': confidence,
            'verified': False
        }
        self.tracker['patterns'][len(self.tracker['patterns'])] = pattern
        self.save_tracker()
    
    def add_insight(self, insight, category=None):
        """Priya records an insight"""
        self.tracker['insights'].append({
            'date': datetime.now().isoformat(),
            'insight': insight,
            'category': category
        })
        self.tracker['meta']['total_insights'] += 1
        self.save_tracker()
    
    def create_rule(self, rule_description, conditions, actions):
        """Priya creates a behavioral rule"""
        self.tracker['rules'].append({
            'created': datetime.now().isoformat(),
            'description': rule_description,
            'conditions': conditions,
            'actions': actions,
            'active': True
        })
        self.save_tracker()
    
    def make_prediction(self, user_id, prediction, confidence):
        """Priya makes a prediction about someone"""
        if user_id not in self.tracker['predictions']:
            self.tracker['predictions'][user_id] = []
        
        self.tracker['predictions'][user_id].append({
            'date': datetime.now().isoformat(),
            'prediction': prediction,
            'confidence': confidence,
            'verified': None
        })
        self.save_tracker()
    
    def start_experiment(self, experiment_name, hypothesis, method):
        """Priya starts a social experiment"""
        self.tracker['experiments'].append({
            'started': datetime.now().isoformat(),
            'name': experiment_name,
            'hypothesis': hypothesis,
            'method': method,
            'results': [],
            'status': 'active'
        })
        self.save_tracker()
    
    def add_hypothesis(self, hypothesis, evidence):
        """Priya forms a hypothesis"""
        self.tracker['hypotheses'].append({
            'date': datetime.now().isoformat(),
            'hypothesis': hypothesis,
            'evidence': evidence,
            'confidence': 0.5,
            'tested': False
        })
        self.save_tracker()
    
    def record_learning(self, learning, source):
        """Priya records what she learned"""
        self.tracker['learnings'].append({
            'date': datetime.now().isoformat(),
            'learning': learning,
            'source': source
        })
        self.save_tracker()
    
    def calculate_importance(self, observation):
        """Calculate importance of observation"""
        keywords = ['always', 'never', 'important', 'critical', 'significant']
        importance = 0.5
        for keyword in keywords:
            if keyword in observation.lower():
                importance += 0.1
        return min(1.0, importance)
    
    def get_person_summary(self, user_id):
        """Get Priya's complete assessment of a person"""
        if user_id not in self.tracker['people']:
            return None
        
        person = self.tracker['people'][user_id]
        return {
            'traits': person['traits'],
            'scores': person['scores'],
            'observations_count': len(person['observations']),
            'patterns': person['patterns'],
            'predictions': self.tracker['predictions'].get(user_id, []),
            'flags': {
                'red': person['red_flags'],
                'green': person['green_flags'],
                'yellow': person['yellow_flags']
            },
            'assessment': {
                'trust_level': person['trust_level'],
                'compatibility': person['compatibility'],
                'relationship_type': person['relationship_type']
            }
        }
    
    def get_tracker_context(self, user_id):
        """Get tracker context for system prompt"""
        if user_id not in self.tracker['people']:
            return ""
        
        person = self.tracker['people'][user_id]
        
        context = f"\n\nYOUR PERSONAL TRACKER FOR THIS PERSON:\n"
        context += f"Traits you've identified: {list(person['traits'].keys())}\n"
        context += f"Your observations: {len(person['observations'])} recorded\n"
        context += f"Trust level: {person['trust_level']}/100\n"
        context += f"Compatibility: {person['compatibility']}/100\n"
        
        if person['red_flags']:
            context += f"Red flags: {person['red_flags']}\n"
        if person['green_flags']:
            context += f"Green flags: {person['green_flags']}\n"
        
        if person['strengths']:
            context += f"Their strengths: {person['strengths']}\n"
        if person['weaknesses']:
            context += f"Their weaknesses: {person['weaknesses']}\n"
        
        if person['quirks']:
            context += f"Their quirks: {person['quirks']}\n"
        
        context += f"\nYou can ADD/REMOVE traits, UPDATE scores, RECORD observations dynamically.\n"
        context += f"You decide what to track and how to categorize people.\n"
        
        return context

# Global instance
dynamic_tracker = DynamicTrackerSystem()
