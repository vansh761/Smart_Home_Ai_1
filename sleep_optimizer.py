"""
Sleep & Comfort Optimizer Module
---------------------------------
Analyzes room conditions (temp, noise, light) and produces
a sleep quality score + actionable recommendations.
Model: Rule-based + weighted scoring (expandable to ML).
"""

from datetime import datetime


class SleepOptimizer:
    """
    Computes sleep quality scores and recommends optimal
    room conditions based on sleep science research.

    Ideal ranges (science-backed):
      Temperature: 16–19°C (60–67°F)
      Noise:       < 30 dB
      Light:       < 10 lux (near darkness)
    """

    IDEAL = {
        'temperature': {'min': 16, 'max': 19, 'optimal': 18},
        'noise':       {'min': 0,  'max': 30, 'optimal': 20},
        'light':       {'min': 0,  'max': 10, 'optimal': 5},
    }

    # Comfort profiles (user-adjustable via adaptive memory)
    PROFILES = {
        'default':   {'temp_pref': 18, 'noise_pref': 25, 'light_pref': 0},
        'warm':      {'temp_pref': 21, 'noise_pref': 30, 'light_pref': 5},
        'cool':      {'temp_pref': 16, 'noise_pref': 20, 'light_pref': 0},
        'white_noise': {'temp_pref': 18, 'noise_pref': 40, 'light_pref': 0},
    }

    def __init__(self):
        self._user_profiles = {}

    def get_current_score(self, state: dict) -> dict:
        """Compute current sleep quality score from room state."""
        temp   = state.get('temperature', 22)
        noise  = state.get('noise_level', 40)
        light  = state.get('light_level', 50)

        temp_score  = self._score_metric('temperature', temp)
        noise_score = self._score_metric('noise', noise)
        light_score = self._score_metric('light', light)

        overall = round((temp_score * 0.4 + noise_score * 0.35 + light_score * 0.25), 1)

        return {
            'score':       overall,
            'grade':       self._grade(overall),
            'components':  {
                'temperature': {'value': temp,  'score': temp_score,  'unit': '°C'},
                'noise':       {'value': noise, 'score': noise_score, 'unit': 'dB'},
                'light':       {'value': light, 'score': light_score, 'unit': 'lux'},
            },
            'summary':     self._summary(overall)
        }

    def optimize(self, conditions: dict) -> dict:
        """
        Analyze conditions and return recommendations.
        Also returns an 'apply' flag for auto-application.
        """
        temp   = conditions.get('temperature', 22)
        noise  = conditions.get('noise', 40)
        light  = conditions.get('light', 50)
        user   = conditions.get('user_id', 'default')

        profile  = self._user_profiles.get(user, self.PROFILES['default'])
        score    = self.get_current_score({'temperature': temp, 'noise_level': noise, 'light_level': light})
        recs     = []
        changes  = {}

        # Temperature
        if temp > self.IDEAL['temperature']['max']:
            target = profile.get('temp_pref', self.IDEAL['temperature']['optimal'])
            recs.append(f'Lower temperature to {target}°C for better sleep')
            changes['temperature'] = target
            changes['ac']          = 'on'
        elif temp < self.IDEAL['temperature']['min']:
            target = profile.get('temp_pref', 20)
            recs.append(f'Raise temperature to {target}°C')
            changes['temperature'] = target
            changes['heater']      = 'on'

        # Noise
        if noise > self.IDEAL['noise']['max']:
            recs.append('Activate white noise machine or close windows')
            changes['white_noise'] = 'on'

        # Light
        if light > self.IDEAL['light']['max']:
            recs.append('Dim lights to minimum or activate blackout mode')
            changes['lights'] = 0

        # Night mode
        hour = datetime.now().hour
        if 22 <= hour or hour < 6:
            recs.append('Enable sleep mode: reducing all stimulation')
            changes['sleep_mode'] = True

        return {
            'score':           score,
            'recommendations': changes,
            'advice':          recs if recs else ['Environment is already optimized for sleep ✓'],
            'apply':           score['score'] < 70,
            'user_id':         user
        }

    def update_profile(self, user_id: str, preferences: dict):
        """Store user-specific comfort preferences."""
        self._user_profiles[user_id] = preferences

    # ── Internal scoring ─────────────────────────────────────
    def _score_metric(self, metric: str, value: float) -> float:
        """Score 0-100 based on distance from ideal range."""
        ideal  = self.IDEAL[metric]
        opt    = ideal['optimal']
        # Perfect score within range
        if ideal['min'] <= value <= ideal['max']:
            deviation = abs(value - opt) / max(ideal['max'] - ideal['min'], 1)
            return round(100 - deviation * 30, 1)
        # Penalize outside range
        if value < ideal['min']:
            dist = ideal['min'] - value
        else:
            dist = value - ideal['max']
        return max(0, round(100 - dist * 8, 1))

    def _grade(self, score: float) -> str:
        if score >= 90: return 'Excellent'
        if score >= 75: return 'Good'
        if score >= 60: return 'Fair'
        if score >= 45: return 'Poor'
        return 'Very Poor'

    def _summary(self, score: float) -> str:
        if score >= 90: return 'Your room is perfectly set for deep sleep'
        if score >= 75: return 'Good sleep conditions with minor improvements possible'
        if score >= 60: return 'Sleep quality may be affected — adjustments recommended'
        return 'Environment not conducive to restful sleep — action needed'
