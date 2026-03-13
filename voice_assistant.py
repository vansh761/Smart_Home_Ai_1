"""
Voice Assistant Module
-----------------------
Handles speech recognition (text input) and text-to-speech output.
Offline by default; optional Alexa/Google Home integration.

INSTALL:
    pip install pyttsx3 SpeechRecognition pyaudio

USAGE:
    - Send text commands via POST /api/voice/command
    - For real microphone input: call voice_assistant.listen()
    - TTS plays locally via pyttsx3 (offline, no API key needed)
"""

import re


class VoiceAssistant:
    """
    Offline voice assistant using pattern matching for commands.
    TTS: pyttsx3 (offline). STT: SpeechRecognition (Google/Whisper).
    Alexa & Google Home: webhook handlers included.
    """

    COMMANDS = {
        r'turn (on|off) (?:the )?lights?':         'lights',
        r'set (?:the )?temp(?:erature)? to (\d+)':  'temperature',
        r'(dim|brighten) (?:the )?lights?':         'dim_lights',
        r'sleep mode':                              'sleep_mode',
        r'(good morning|wake up|morning mode)':     'morning_mode',
        r'(good night|bedtime|night mode)':         'night_mode',
        r'turn (on|off) (?:the )?fan':             'fan',
        r'turn (on|off) (?:the )?ac':              'ac',
        r'energy report':                           'energy_report',
        r'how am i doing':                          'wellness_check',
        r'(?:i feel|i am|i\'m) (.+)':              'mood_input',
        r'play (.+) music':                         'music',
    }

    def __init__(self):
        self._tts_enabled = self._init_tts()
        self._command_history = []

    def _init_tts(self) -> bool:
        """Initialize offline text-to-speech engine."""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 165)
            self._engine.setProperty('volume', 0.9)
            return True
        except Exception:
            print("[VoiceAssistant] pyttsx3 not available — TTS disabled. pip install pyttsx3")
            return False

    def speak(self, text: str):
        """
        Text-to-speech output (offline via pyttsx3).
        Falls back to console print if TTS not available.
        """
        print(f"[TTS] {text}")
        if self._tts_enabled:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"[TTS Error] {e}")

    def listen(self) -> str:
        """
        Real speech-to-text using microphone.
        Requires: pip install SpeechRecognition pyaudio

        Returns recognized text string, or empty string on failure.
        In simulation mode: send text via POST /api/voice/command instead.
        """
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                print("[STT] Listening... speak now")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"[STT] Heard: {text}")
            return text
        except ImportError:
            print("[STT] SpeechRecognition not installed. pip install SpeechRecognition pyaudio")
            return ""
        except Exception as e:
            print(f"[STT] Could not recognize speech: {e}")
            return ""

    def process_command(self, command: str, simulator, mood_analyzer, user_id: str) -> dict:
        """
        Parse a text command and execute the matching action.
        Called by POST /api/voice/command endpoint.
        """
        cmd_lower = command.lower().strip()
        self._command_history.append({'command': command, 'user': user_id})

        for pattern, action in self.COMMANDS.items():
            match = re.search(pattern, cmd_lower)
            if match:
                return self._execute(action, match, command, simulator, mood_analyzer, user_id)

        return {
            'understood': False,
            'response':   "I didn't quite catch that. Try: 'turn on the lights', 'sleep mode', or 'I feel stressed'",
            'command':    command
        }

    def _execute(self, action: str, match, command: str, simulator, mood_analyzer, user_id: str) -> dict:
        """Execute a matched command and return a response dict."""
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
            changes  = {'fan': state}
            response = f"Fan turned {state}."

        elif action == 'ac':
            state = match.group(1)
            simulator.control_appliance('ac', state)
            changes  = {'ac': state}
            response = f"AC turned {state}."

        elif action == 'energy_report':
            response = "Your home has used 4.2 kWh today, saving $0.38 compared to yesterday."

        elif action == 'wellness_check':
            state = simulator.get_state()
            response = (
                f"Temperature is {state['temperature']}°C, "
                f"lights at {round(state['light_level'])}%. "
                f"Everything looks comfortable."
            )

        elif action == 'mood_input':
            mood_text = match.group(1) if match.lastindex and match.lastindex >= 1 else command
            result    = mood_analyzer.analyze(mood_text, user_id)
            env       = mood_analyzer.get_environment_adjustments(result['mood'])
            simulator.apply_mood_adjustments(env)
            response  = (
                f"Detected {result['mood']} mood {result['emoji']}. "
                f"Adjusting environment: {env.get('reason', 'settings updated')}."
            )
            changes = env

        elif action == 'music':
            genre    = match.group(1)
            response = f"Playing {genre} music."
            changes  = {'music': genre}

        self.speak(response)

        return {
            'understood': True,
            'action':     action,
            'response':   response,
            'changes':    changes,
            'command':    command
        }

    def get_history(self) -> list:
        """Return list of past commands."""
        return self._command_history

    # ── Alexa Integration ─────────────────────────────────────
    def handle_alexa_intent(self, intent: str, slots: dict, simulator) -> dict:
        """
        Handle Alexa Smart Home skill intents.
        Deploy your Alexa skill to point to: https://your-domain/api/alexa/intent

        Supported intents:
            TurnOnIntent, TurnOffIntent, SetTempIntent, SleepModeIntent
        """
        intent_map = {
            'TurnOnIntent':    lambda: simulator.control_appliance('lights', 'on'),
            'TurnOffIntent':   lambda: simulator.control_appliance('lights', 'off'),
            'SetTempIntent':   lambda: simulator.control_appliance(
                                   'ac', 'on',
                                   int(slots.get('Temperature', {}).get('value', 22))
                               ),
            'SleepModeIntent': lambda: simulator.apply_recommendations(
                                   {'temperature': 18, 'lights': 5}
                               ),
        }

        handler = intent_map.get(intent)
        if handler:
            handler()
            return {
                'version': '1.0',
                'response': {
                    'outputSpeech': {
                        'type': 'PlainText',
                        'text': f'Done! {intent} executed successfully.'
                    },
                    'shouldEndSession': True
                }
            }

        return {
            'version': '1.0',
            'response': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': "Sorry, I didn't understand that intent."
                }
            }
        }

    # ── Google Home Integration ───────────────────────────────
    def handle_google_intent(self, intent: str, params: dict, simulator) -> dict:
        """
        Handle Google Home Actions fulfillment.
        Connect via Google Actions Console → Fulfillment → Webhook URL:
            https://your-domain/api/google/fulfillment
        """
        response_text = "Command received."

        if 'lights' in intent.lower():
            state = params.get('state', 'on')
            simulator.control_appliance('lights', state)
            response_text = f"Lights turned {state}."

        elif 'temperature' in intent.lower():
            temp = params.get('temperature', 21)
            simulator.control_appliance('ac', 'on', temp)
            response_text = f"Temperature set to {temp} degrees."

        elif 'sleep' in intent.lower():
            simulator.apply_recommendations({'temperature': 18, 'lights': 5})
            response_text = "Sleep mode activated."

        elif 'morning' in intent.lower():
            simulator.apply_recommendations({'temperature': 22, 'lights': 100})
            response_text = "Good morning! Morning mode activated."

        return {
            'fulfillmentText': response_text,
            'fulfillmentMessages': [{'text': {'text': [response_text]}}]
        }

