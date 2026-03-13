"""
Mood Analyzer Module
--------------------
Detects emotional state from text (voice transcript) using
sentiment analysis. Maps mood to environment adjustments.

Model: TextBlob sentiment + keyword matching.
Upgrade path: Replace with transformers (RoBERTa, DistilBERT)
              or use Hume AI / AWS Comprehend for voice audio.
"""

import random
from collections import deque
from datetime import datetime


class MoodAnalyzer:
    """
    Analyzes text for emotional tone and maps to smart home adjustments.
    Maintains per-user mood history (rolling 50 entries).
    """

    MOOD_KEYWORDS = {
        'stressed':  ['stressed', 'anxious', 'overwhelmed', 'worried', 'nervous', 'tense', 'panic'],
        'tired':     ['tired', 'exhausted', 'sleepy', 'fatigue', 'drained', 'weary', 'drowsy'],
        'happy':     ['happy', 'great', 'wonderful', 'excited', 'joy', 'fantastic', 'energized', 'amazing'],
        'sad':       ['sad', 'depressed', 'unhappy', 'miserable', 'down', 'blue', 'gloomy', 'upset'],
        'focused':   ['focus', 'working', 'concentrate', 'study', 'productive', 'work'],
        'relaxed':   ['relaxed', 'calm', 'peaceful', 'chill', 'comfortable', 'content', 'serene'],
        'angry':     ['angry', 'frustrated', 'mad', 'furious', 'irritated', 'annoyed'],
    }

    # Environment adjustments per mood
    MOOD_ENVIRONMENT = {
        'stressed': {
            'temperature': 20,
            'lights':      40,
            'light_color': 'warm_white',  # 2700K
            'fan':         'low',
            'music':       'ambient',
            'reason':      'Calm, soft environment to reduce stress'
        },
        'tired': {
            'temperature': 18,
            'lights':      20,
            'light_color': 'very_warm',   # 2200K
            'fan':         'off',
            'music':       'sleep',
            'reason':      'Preparing for rest — lowering stimulation'
        },
        'happy': {
            'temperature': 22,
            'lights':      80,
            'light_color': 'daylight',    # 5000K
            'fan':         'medium',
            'music':       'upbeat',
            'reason':      'Energetic environment matching your great mood'
        },
        'sad': {
            'temperature': 22,
            'lights':      60,
            'light_color': 'warm_white',
            'fan':         'off',
            'music':       'comforting',
            'reason':      'Warm, cozy environment to uplift mood'
        },
        'focused': {
            'temperature': 20,
            'lights':      100,
            'light_color': 'cool_white',  # 4000K
            'fan':         'low',
            'music':       'instrumental',
            'reason':      'Bright, cool environment for peak focus'
        },
        'relaxed': {
            'temperature': 21,
            'lights':      50,
            'light_color': 'warm_white',
            'fan':         'low',
            'music':       'lofi',
            'reason':      'Maintaining your relaxed state'
        },
        'angry': {
            'temperature': 19,
            'lights':      40,
            'light_color': 'warm_white',
            'fan':         'medium',
            'music':       'calm',
            'reason':      'Cooling environment to help de-escalate'
        },
        'neutral': {
            'temperature': 21,
            'lights':      70,
            'light_color': 'daylight',
            'fan':         'off',
            'music':       'off',
            'reason':      'Standard comfortable environment'
        }
    }

    def __init__(self):
        self._histories  = {}         # user_id → deque of mood events
        self._current    = {}         # user_id → latest mood
        self._global_mood = 'neutral'

    def analyze(self, text: str, user_id: str = 'user1') -> dict:
        """
        Detect mood from text. Returns mood label, confidence, score.
        """
        if not text.strip():
            return self._neutral_result(user_id)

        text_lower = text.lower()

        # Keyword matching (fast, interpretable)
        scores = {}
        for mood, keywords in self.MOOD_KEYWORDS.items():
            hit = sum(1 for kw in keywords if kw in text_lower)
            if hit:
                scores[mood] = hit

        # Fallback: basic sentiment polarity
        polarity = self._simple_sentiment(text_lower)

        if scores:
            detected = max(scores, key=scores.get)
            confidence = min(0.95, 0.5 + scores[detected] * 0.15)
        elif polarity > 0.3:
            detected, confidence = 'happy', 0.65
        elif polarity < -0.3:
            detected, confidence = 'sad', 0.65
        else:
            detected, confidence = 'neutral', 0.80

        score = self._mood_to_score(detected, polarity)

        result = {
            'mood':        detected,
            'confidence':  round(confidence, 2),
            'score':       score,
            'polarity':    round(polarity, 3),
            'user_id':     user_id,
            'timestamp':   datetime.now().isoformat(),
            'emoji':       self._mood_emoji(detected)
        }

        # Update history
        if user_id not in self._histories:
            self._histories[user_id] = deque(maxlen=50)
        self._histories[user_id].appendleft(result)
        self._current[user_id] = result
        self._global_mood = detected

        return result

    def get_environment_adjustments(self, mood: str) -> dict:
        return self.MOOD_ENVIRONMENT.get(mood, self.MOOD_ENVIRONMENT['neutral'])

    def get_current_mood(self) -> dict:
        if not self._current:
            return {'mood': 'neutral', 'score': 50, 'emoji': '😐'}
        # Average across users
        moods = list(self._current.values())
        return moods[0] if len(moods) == 1 else {
            'mood':  'mixed',
            'score': round(sum(m['score'] for m in moods) / len(moods), 1),
            'emoji': '🎭',
            'users': moods
        }

    def get_history(self, user_id: str) -> list:
        hist = self._histories.get(user_id, deque())
        return list(hist)

    # ── Internal helpers ──────────────────────────────────────
    def _simple_sentiment(self, text: str) -> float:
        """Very simple lexicon-based sentiment (-1 to +1). Replace with TextBlob."""
        positives = ['good','great','love','excellent','wonderful','amazing','happy','enjoy','glad','fantastic']
        negatives = ['bad','hate','awful','terrible','horrible','sad','angry','frustrated','wrong','fail']
        pos = sum(1 for w in positives if w in text)
        neg = sum(1 for w in negatives if w in text)
        total = pos + neg
        if total == 0: return 0.0
        return (pos - neg) / total

    def _mood_to_score(self, mood: str, polarity: float) -> float:
        """Mood wellness score 0-100."""
        base = {
            'happy': 90, 'relaxed': 80, 'focused': 75, 'neutral': 60,
            'stressed': 35, 'tired': 40, 'sad': 30, 'angry': 25
        }.get(mood, 60)
        return round(max(0, min(100, base + polarity * 10)), 1)

    def _mood_emoji(self, mood: str) -> str:
        return {
            'happy': '😊', 'relaxed': '😌', 'focused': '🎯', 'neutral': '😐',
            'stressed': '😰', 'tired': '😴', 'sad': '😢', 'angry': '😠'
        }.get(mood, '😐')

    def _neutral_result(self, user_id: str) -> dict:
        return {
            'mood': 'neutral', 'confidence': 1.0, 'score': 60,
            'polarity': 0.0, 'user_id': user_id,
            'timestamp': datetime.now().isoformat(), 'emoji': '😐'
        }

    def record_mood_event(self, user_id: str, mood: str, timestamp: datetime):
        """Called by adaptive memory to log mood events."""
        pass  # History already stored in analyze()
