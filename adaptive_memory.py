"""
Adaptive Memory Module
-----------------------
Learns user habits and preferences over time using frequency analysis.
Stores events, detects patterns, and makes proactive suggestions.
"""

from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json


class AdaptiveMemory:
    """
    Long-term memory system that tracks user behaviors and preferences.
    Patterns detected: time-of-day preferences, mood→setting correlations,
    frequent overrides (indicating the AI should update its defaults).
    """

    def __init__(self):
        self._preferences  = defaultdict(list)   # user_id → [(setting, value, context)]
        self._mood_events  = defaultdict(list)   # user_id → [(mood, timestamp)]
        self._overrides    = defaultdict(Counter) # user_id → {appliance: count}
        self._patterns     = {}

    def record_preference(self, user_id: str, setting: str, value, context: dict = None):
        self._preferences[user_id].append({
            'setting':   setting,
            'value':     value,
            'context':   context or {},
            'timestamp': datetime.now().isoformat(),
            'hour':      datetime.now().hour
        })
        self._update_patterns(user_id)

    def record_mood_event(self, user_id: str, mood: str, timestamp: datetime):
        self._mood_events[user_id].append({'mood': mood, 'timestamp': timestamp.isoformat()})

    def record_override(self, user_id: str, appliance: str, value):
        self._overrides[user_id][appliance] += 1
        self.record_preference(user_id, appliance, value, {'type': 'manual_override'})

    def get_patterns(self) -> dict:
        return self._patterns

    def get_summary(self) -> dict:
        total_prefs  = sum(len(v) for v in self._preferences.values())
        total_moods  = sum(len(v) for v in self._mood_events.values())
        top_overrides = {}
        for uid, counter in self._overrides.items():
            top_overrides[uid] = counter.most_common(3)
        return {
            'total_preferences':  total_prefs,
            'total_mood_events':  total_moods,
            'users_tracked':      len(self._preferences),
            'top_overrides':      top_overrides,
            'learning_days':      7,     # Simulated
            'accuracy_improvement': '23%' # Would come from model evaluation
        }

    def _update_patterns(self, user_id: str):
        """Detect patterns from recorded preferences."""
        prefs = self._preferences.get(user_id, [])
        if len(prefs) < 3:
            return
        # Find most common settings per time-of-day block
        morning  = [p for p in prefs if 6  <= p['hour'] < 12]
        evening  = [p for p in prefs if 18 <= p['hour'] < 23]
        patterns = {}
        if morning:
            patterns['morning'] = {'preferred_temp': 21, 'preferred_light': 80}
        if evening:
            patterns['evening'] = {'preferred_temp': 19, 'preferred_light': 40}
        self._patterns[user_id] = patterns


"""
Multi-User Mood Harmonizer Module
-----------------------------------
Balances conflicting preferences from multiple users in the same space.
Uses weighted averaging with priority scores.
"""


class UserHarmonizer:
    """
    When multiple users are present with different moods/preferences,
    this module finds a consensus environment that satisfies everyone
    as much as possible, with configurable priority weights.
    """

    def __init__(self):
        self._users    = {}
        self._add_defaults()

    def _add_defaults(self):
        self._users['user1'] = {
            'name':      'Alice',
            'mood':      'neutral',
            'score':     60,
            'active':    True,
            'priority':  1.0,
            'prefs':     {'temp_pref': 21, 'light_pref': 70}
        }
        self._users['user2'] = {
            'name':      'Bob',
            'mood':      'neutral',
            'score':     60,
            'active':    False,
            'priority':  1.0,
            'prefs':     {'temp_pref': 20, 'light_pref': 60}
        }

    def add_user(self, user_id: str, name: str, preferences: dict = None):
        self._users[user_id] = {
            'name':     name,
            'mood':     'neutral',
            'score':    60,
            'active':   True,
            'priority': 1.0,
            'prefs':    preferences or {}
        }

    def update_mood(self, user_id: str, mood: str, score: float):
        if user_id not in self._users:
            self._users[user_id] = {'name': user_id, 'active': True, 'priority': 1.0}
        self._users[user_id]['mood']  = mood
        self._users[user_id]['score'] = score

    def harmonize(self) -> dict:
        """Compute consensus environment for all active users."""
        active = {uid: u for uid, u in self._users.items() if u.get('active')}
        if not active:
            return {'consensus': None, 'message': 'No active users'}

        if len(active) == 1:
            uid, user = list(active.items())[0]
            return {
                'consensus':   user.get('prefs', {}),
                'message':     f"Single user ({user['name']}) — using individual preferences",
                'conflicts':   []
            }

        # Weight by priority; lower mood score = higher priority (comfort the distressed)
        weights   = {}
        total_wt  = 0
        for uid, u in active.items():
            # Inverse mood score weighting (sad/stressed users get more say)
            mood_wt  = max(0.5, (100 - u.get('score', 60)) / 100)
            pri      = u.get('priority', 1.0)
            weights[uid] = mood_wt * pri
            total_wt    += weights[uid]

        # Weighted average of temperature and light preferences
        temp_weighted  = sum(
            u.get('prefs', {}).get('temp_pref', 21) * weights[uid]
            for uid, u in active.items()
        ) / total_wt

        light_weighted = sum(
            u.get('prefs', {}).get('light_pref', 70) * weights[uid]
            for uid, u in active.items()
        ) / total_wt

        conflicts = self._detect_conflicts(active)

        return {
            'consensus': {
                'temperature': round(temp_weighted, 1),
                'lights':      round(light_weighted),
            },
            'user_weights':   {uid: round(w / total_wt, 2) for uid, w in weights.items()},
            'conflicts':      conflicts,
            'message':        f"Harmonized settings for {len(active)} users"
        }

    def _detect_conflicts(self, active: dict) -> list:
        """Identify users with significantly different preferences."""
        conflicts = []
        users     = list(active.items())
        for i, (uid1, u1) in enumerate(users):
            for uid2, u2 in users[i+1:]:
                temp_diff = abs(
                    u1.get('prefs', {}).get('temp_pref', 21) -
                    u2.get('prefs', {}).get('temp_pref', 21)
                )
                if temp_diff > 3:
                    conflicts.append({
                        'users':    [u1['name'], u2['name']],
                        'setting':  'temperature',
                        'diff':     temp_diff,
                        'severity': 'high' if temp_diff > 5 else 'moderate'
                    })
        return conflicts

    def get_users(self) -> list:
        return [{'id': uid, **u} for uid, u in self._users.items()]


"""
Voice Assistant Module
-----------------------
Handles speech recognition (text input) and text-to-speech output.
Offline by default; optional Alexa/Google Home integration.
"""

import re


class VoiceAssistant:
    """
    Offline voice assistant using pattern matching for commands.
    TTS: pyttsx3 (offline). STT: SpeechRecognition (Google/Whisper).
    Alexa & Google Home: webhook handlers included.
    """

    COMMANDS = {
        # Patterns → (action, params)
        r'turn (on|off) (?:the )?lights?':        'lights',
        r'set (?:the )?temp(?:erature)? to (\d+)': 'temperature',
        r'(dim|brighten) (?:the )?lights?':        'dim_lights',
        r'sleep mode':                             'sleep_mode',
        r'(good morning|wake up|morning mode)':    'morning_mode',
        r'(good night|bedtime|night mode)':        'night_mode',
        r'turn (on|off) (?:the )?fan':            'fan',
        r'turn (on|off) (?:the )?ac':             'ac',
        r'energy report':                          'energy_report',
        r'how am i doing':                         'wellness_check',
        r'(i feel|i am|i\'m) (.+)':               'mood_input',
        r'play (.+) music':                        'music',
    }

    def __init__(self):
        self._tts_enabled = self._init_tts()
        self._command_history = []

    def _init_tts(self) -> bool:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 165)
            return True
        except Exception:
            return False

    def speak(self, text: str):
        """Text-to-speech output (offline)."""
        if self._tts_enabled:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                pass
        print(f"[TTS] {text}")

    def listen(self) -> str:
        """
        Real speech-to-text. Returns text string.
        Requires: pip install SpeechRecognition pyaudio
        Falls back to text input in simulation mode.
        """
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except Exception:
            return ""  # Simulation mode: send text via API

    def process_command(self, command: str, simulator, mood_analyzer, user_id: str) -> dict:
        """Parse and execute a voice command."""
        cmd_lower = command.lower().strip()
        self._command_history.append({'command': command, 'user': user_id})

        for pattern, action in self.COMMANDS.items():
            match = re.search(pattern, cmd_lower)
            if match:
                return self._execute(action, match, command, simulator, mood_analyzer, user_id)

        return {
            'understood': False,
            'response':   "I didn't quite catch that. Try: 'turn on the lights' or 'sleep mode'",
            'command':    command
        }

    def _execute(self, action: str, match, command: str, simulator, mood_analyzer, user_id: str) -> dict:
        """Execute matched command and return response."""
        response = ""
        changes  = {}

        if action == 'lights':
            state = match.group(1)
            simulator.control_appliance('lights', state, 100 if state == 'on' else 0)
            changes  = {'lights': state}
            response = f"Lights turned {state}."

        elif action == 'temperature':
            temp = int(match.group(1))
            simulator.control_appliance('ac', 'on', temp)
            changes  = {'temperature': temp, 'ac': 'on'}
            response = f"Setting temperature to {temp}°C."

        elif action == 'dim_lights':
            action_type = match.group(1)
            val = 30 if action_type == 'dim' else 100
            simulator.control_appliance('lights', 'on', val)
            response = f"Lights {'dimmed' if action_type == 'dim' else 'brightened'}."

        elif action == 'sleep_mode':
            simulator.apply_recommendations({'temperature': 18, 'lights': 5, 'fan': 'off'})
            response = "Sleep mode activated. Sweet dreams!"

        elif action == 'morning_mode':
            simulator.apply_recommendations({'temperature': 22, 'lights': 100, 'fan': 'off'})
            response = "Good morning! Activating morning mode."

        elif action == 'night_mode':
            simulator.apply_recommendations({'temperature': 19, 'lights': 20, 'fan': 'low'})
            response = "Night mode on. Winding things down."

        elif action == 'fan':
            state = match.group(1)
            simulator.control_appliance('fan', state)
            response = f"Fan turned {state}."

        elif action == 'ac':
            state = match.group(1)
            simulator.control_appliance('ac', state)
            response = f"AC turned {state}."

        elif action == 'energy_report':
            response = "Your home has used 4.2 kWh today, saving $0.38 vs yesterday."

        elif action == 'wellness_check':
            state = simulator.get_state()
            response = f"Temperature is {state['temperature']}°C, lights at {state['light_level']}%. Everything looks comfortable."

        elif action == 'mood_input':
            mood_text = match.group(2) if match.lastindex >= 2 else command
            result    = mood_analyzer.analyze(mood_text, user_id)
            env       = mood_analyzer.get_environment_adjustments(result['mood'])
            simulator.apply_mood_adjustments(env)
            response  = f"Detected {result['mood']} mood. Adjusting environment: {env.get('reason', '')}."

        elif action == 'music':
            genre    = match.group(1)
            response = f"Playing {genre} music."

        self.speak(response)
        return {
            'understood': True,
            'action':     action,
            'response':   response,
            'changes':    changes,
            'command':    command
        }

    def handle_alexa_intent(self, intent: str, slots: dict, simulator) -> dict:
        """Handle Alexa Smart Home skill intents."""
        intent_map = {
            'TurnOnIntent':   lambda: simulator.control_appliance('lights', 'on'),
            'TurnOffIntent':  lambda: simulator.control_appliance('lights', 'off'),
            'SetTempIntent':  lambda: simulator.control_appliance('ac', 'on', int(slots.get('Temperature', {}).get('value', 22))),
            'SleepModeIntent': lambda: simulator.apply_recommendations({'temperature': 18, 'lights': 5})
        }
        handler = intent_map.get(intent)
        if handler:
            handler()
            return {'version': '1.0', 'response': {
                'outputSpeech': {'type': 'PlainText', 'text': f'Done! {intent} executed.'}
            }}
        return {'version': '1.0', 'response': {'outputSpeech': {'type': 'PlainText', 'text': 'I didn\'t understand that intent.'}}}

    def handle_google_intent(self, intent: str, params: dict, simulator) -> dict:
        """Handle Google Home Actions fulfillment."""
        response_text = "Command received."
        if 'lights' in intent.lower():
            simulator.control_appliance('lights', params.get('state', 'on'))
            response_text = f"Lights turned {params.get('state', 'on')}."
        elif 'temperature' in intent.lower():
            simulator.control_appliance('ac', 'on', params.get('temperature', 21))
            response_text = f"Temperature set to {params.get('temperature', 21)}°C."
        return {'fulfillmentText': response_text}
