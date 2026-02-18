"""
Minimal Custom AI Engine - Just to show the complexity
This is a TINY fraction of what's needed for a real AI model
"""
import numpy as np
import json
from typing import List, Dict, Tuple
import random
import math

class MiniTransformer:
    """Ultra-simplified transformer model (not production ready)"""
    
    def __init__(self, vocab_size: int = 10000, d_model: int = 512, n_heads: int = 8):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        
        # Initialize weights (normally loaded from training)
        self.embedding = np.random.randn(vocab_size, d_model) * 0.1
        self.pos_encoding = self._positional_encoding(1000, d_model)
        
        # Attention weights (simplified)
        self.w_q = np.random.randn(d_model, d_model) * 0.1
        self.w_k = np.random.randn(d_model, d_model) * 0.1
        self.w_v = np.random.randn(d_model, d_model) * 0.1
        self.w_o = np.random.randn(d_model, d_model) * 0.1
        
        # Feed forward
        self.w1 = np.random.randn(d_model, d_model * 4) * 0.1
        self.w2 = np.random.randn(d_model * 4, d_model) * 0.1
        
        # Layer norms
        self.ln1_weight = np.ones(d_model)
        self.ln2_weight = np.ones(d_model)
        
        # Vocabulary (simplified)
        self.vocab = self._build_vocab()
        self.token_to_id = {token: i for i, token in enumerate(self.vocab)}
        self.id_to_token = {i: token for i, token in enumerate(self.vocab)}
    
    def _build_vocab(self) -> List[str]:
        """Build a simple vocabulary"""
        # This would normally be built from training data
        common_words = [
            "hello", "hi", "how", "are", "you", "i", "am", "good", "bad", "okay",
            "yes", "no", "maybe", "sure", "thanks", "welcome", "sorry", "please",
            "what", "when", "where", "why", "who", "can", "will", "would", "could",
            "the", "a", "an", "and", "or", "but", "if", "then", "so", "because",
            "love", "like", "hate", "want", "need", "have", "get", "go", "come",
            "see", "know", "think", "feel", "say", "tell", "ask", "answer",
            "happy", "sad", "angry", "excited", "tired", "hungry", "thirsty",
            "priya", "yaar", "arre", "acha", "chai", "bollywood", "india"
        ]
        
        # Add numbers, punctuation, special tokens
        vocab = ["<pad>", "<unk>", "<start>", "<end>"] + common_words
        vocab += [str(i) for i in range(100)]
        vocab += [".", ",", "!", "?", ":", ";", "'", '"', "(", ")", "[", "]"]
        
        # Pad to vocab_size
        while len(vocab) < self.vocab_size:
            vocab.append(f"<token_{len(vocab)}>")
        
        return vocab[:self.vocab_size]
    
    def _positional_encoding(self, max_len: int, d_model: int) -> np.ndarray:
        """Create positional encodings"""
        pe = np.zeros((max_len, d_model))
        position = np.arange(0, max_len).reshape(-1, 1)
        
        div_term = np.exp(np.arange(0, d_model, 2) * -(math.log(10000.0) / d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        return pe
    
    def tokenize(self, text: str) -> List[int]:
        """Simple tokenization"""
        tokens = text.lower().split()
        return [self.token_to_id.get(token, 1) for token in tokens]  # 1 = <unk>
    
    def detokenize(self, token_ids: List[int]) -> str:
        """Convert token IDs back to text"""
        tokens = [self.id_to_token.get(id, "<unk>") for id in token_ids]
        return " ".join(tokens)
    
    def attention(self, x: np.ndarray) -> np.ndarray:
        """Simplified attention mechanism"""
        seq_len, d_model = x.shape
        
        # Compute Q, K, V
        q = np.dot(x, self.w_q)
        k = np.dot(x, self.w_k)
        v = np.dot(x, self.w_v)
        
        # Scaled dot-product attention
        scores = np.dot(q, k.T) / math.sqrt(d_model)
        
        # Apply causal mask (for autoregressive generation)
        mask = np.triu(np.ones((seq_len, seq_len)), k=1) * -1e9
        scores += mask
        
        # Softmax
        attention_weights = self._softmax(scores)
        
        # Apply attention to values
        output = np.dot(attention_weights, v)
        
        # Output projection
        return np.dot(output, self.w_o)
    
    def feed_forward(self, x: np.ndarray) -> np.ndarray:
        """Feed forward network"""
        hidden = np.dot(x, self.w1)
        hidden = self._relu(hidden)
        return np.dot(hidden, self.w2)
    
    def layer_norm(self, x: np.ndarray, weight: np.ndarray) -> np.ndarray:
        """Layer normalization"""
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        return weight * (x - mean) / (std + 1e-6)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax activation"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation"""
        return np.maximum(0, x)
    
    def forward(self, token_ids: List[int]) -> np.ndarray:
        """Forward pass through the model"""
        seq_len = len(token_ids)
        
        # Embedding + positional encoding
        x = self.embedding[token_ids] + self.pos_encoding[:seq_len]
        
        # Transformer block (simplified - normally multiple layers)
        # Self-attention
        attn_output = self.attention(x)
        x = self.layer_norm(x + attn_output, self.ln1_weight)
        
        # Feed forward
        ff_output = self.feed_forward(x)
        x = self.layer_norm(x + ff_output, self.ln2_weight)
        
        # Output projection to vocabulary
        logits = np.dot(x[-1], self.embedding.T)  # Only last token for generation
        
        return logits
    
    def generate(self, prompt: str, max_length: int = 50) -> str:
        """Generate text (very basic)"""
        token_ids = [2] + self.tokenize(prompt)  # 2 = <start>
        
        for _ in range(max_length):
            if len(token_ids) >= 100:  # Max context
                token_ids = token_ids[-50:]  # Keep last 50 tokens
            
            logits = self.forward(token_ids)
            
            # Simple sampling (temperature = 1.0)
            probabilities = self._softmax(logits)
            next_token = np.random.choice(len(probabilities), p=probabilities)
            
            if next_token == 3:  # <end> token
                break
            
            token_ids.append(next_token)
        
        # Remove special tokens and return
        response_tokens = [t for t in token_ids[len(self.tokenize(prompt))+1:] 
                          if t not in [0, 1, 2, 3]]
        return self.detokenize(response_tokens)

class SimplePersonality:
    """Basic personality system"""
    
    def __init__(self):
        self.responses = {
            "greeting": [
                "Hello yaar! How are you?",
                "Hi there! What's up?",
                "Arre, hello! Nice to see you!"
            ],
            "question": [
                "That's a good question!",
                "Hmm, let me think about that...",
                "Interesting! I think..."
            ],
            "default": [
                "I see what you mean!",
                "That's cool yaar!",
                "Acha, tell me more!"
            ]
        }
    
    def get_response_type(self, text: str) -> str:
        """Classify input type"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["hello", "hi", "hey"]):
            return "greeting"
        elif "?" in text:
            return "question"
        else:
            return "default"
    
    def enhance_response(self, base_response: str, input_text: str) -> str:
        """Add personality to response"""
        response_type = self.get_response_type(input_text)
        personality_response = random.choice(self.responses[response_type])
        
        # Combine if base response is meaningful
        if len(base_response.strip()) > 10:
            return f"{personality_response} {base_response}"
        else:
            return personality_response

class CustomAIEngine:
    """Main custom AI engine"""
    
    def __init__(self):
        print("Initializing custom AI engine...")
        self.model = MiniTransformer()
        self.personality = SimplePersonality()
        print("Custom AI engine ready!")
    
    async def generate_response(self, messages: List[Dict], temperature: float = 0.95) -> str:
        """Generate response using custom model"""
        # Get last user message
        user_message = messages[-1]["content"] if messages else "Hello"
        
        # Generate base response
        base_response = self.model.generate(user_message, max_length=30)
        
        # Add personality
        final_response = self.personality.enhance_response(base_response, user_message)
        
        return final_response
    
    def get_status(self) -> Dict:
        """Get engine status"""
        return {
            "engine": "Custom MiniTransformer",
            "vocab_size": self.model.vocab_size,
            "model_size": "~50MB (tiny)",
            "status": "running"
        }

# This is just a TINY example - real AI engines need:
# - Proper training on massive datasets (100GB-1TB+)
# - Multiple transformer layers (12-96+ layers)
# - Attention mechanisms, layer norms, etc.
# - CUDA/GPU optimization
# - Distributed training infrastructure
# - Tokenization, preprocessing pipelines
# - Safety filters, alignment training
# - And thousands more components...