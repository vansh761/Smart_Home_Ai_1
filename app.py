"""
╔══════════════════════════════════════════════════════════════╗
║         AI SMART HOME INTELLIGENCE SYSTEM                    ║
║         Backend: Flask + AI Modules                          ║
║         Mode: Software-First (Hardware-Ready)                ║
╚══════════════════════════════════════════════════════════════╝

RUNNING:
  pip install flask flask-cors numpy scikit-learn textblob pyttsx3 speechrecognition
  python app.py
  Open: http://localhost:5000

HARDWARE INTEGRATION (later):
  - Connect Raspberry Pi via /api/hardware/connect
  - Smart plugs via /api/appliance/control
  - Sensors via /api/sensors/update
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
try:
    from flask_cors import CORS
    HAS_CORS = True
except ImportError:
    HAS_CORS = False
import json, time, random, math
from datetime import datetime, timedelta
from modules.energy_optimizer import EnergyOptimizer
from modules.sleep_optimizer import SleepOptimizer
from modules.mood_analyzer import MoodAnalyzer
from modules.adaptive_memory import AdaptiveMemory
from modules.user_harmonizer import UserHarmonizer
from modules.voice_assistant import VoiceAssistant
from modules.simulation import HomeSimulator

app = Flask(__name__)
if HAS_CORS:
    CORS(app)

# ─── Initialize all AI modules ────────────────────────────────
energy_optimizer = EnergyOptimizer()
sleep_optimizer  = SleepOptimizer()
mood_analyzer    = MoodAnalyzer()
adaptive_memory  = AdaptiveMemory()
user_harmonizer  = UserHarmonizer()
voice_assistant  = VoiceAssistant()
simulator        = HomeSimulator()

# ─── Dashboard ────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ─── System Status ────────────────────────────────────────────
@app.route('/api/status')
def system_status():
    """Returns full current system state for dashboard refresh."""
    sim_state = simulator.get_state()
    mood      = mood_analyzer.get_current_mood()
    memory    = adaptive_memory.get_summary()
    return jsonify({
        'timestamp':    datetime.now().isoformat(),
        'simulation':   sim_state,
        'mood':         mood,
        'memory':       memory,
        'energy':       energy_optimizer.get_current_stats(),
        'sleep':        sleep_optimizer.get_current_score(sim_state),
        'users':        user_harmonizer.get_users(),
        'mode':         'simulation'   # switches to 'hardware' when connected
    })

# ─── Energy Endpoints ─────────────────────────────────────────
@app.route('/api/energy/predict')
def predict_energy():
    """Predict next 24h energy usage and optimal appliance schedule."""
    hour   = datetime.now().hour
    preds  = energy_optimizer.predict_24h(hour)
    sched  = energy_optimizer.optimize_schedule(preds)
    return jsonify({'predictions': preds, 'schedule': sched})

@app.route('/api/energy/history')
def energy_history():
    """Returns 7-day energy usage history (simulated or real)."""
    return jsonify({'history': energy_optimizer.get_history()})

# ─── Sleep & Comfort Endpoints ────────────────────────────────
@app.route('/api/sleep/optimize', methods=['POST'])
def optimize_sleep():
    """
    Accepts room conditions and returns sleep optimization recommendations.
    Body: { temperature, noise_level, light_level, user_id }
    """
    data  = request.json or {}
    state = simulator.get_state()
    result = sleep_optimizer.optimize({
        'temperature': data.get('temperature', state['temperature']),
        'noise':       data.get('noise_level', state['noise_level']),
        'light':       data.get('light_level', state['light_level']),
        'user_id':     data.get('user_id', 'user1')
    })
    # Apply recommendations to simulator
    if result.get('apply'):
        simulator.apply_recommendations(result['recommendations'])
    return jsonify(result)

@app.route('/api/sleep/score')
def sleep_score():
    return jsonify(sleep_optimizer.get_current_score(simulator.get_state()))

# ─── Mood Endpoints ───────────────────────────────────────────
@app.route('/api/mood/analyze', methods=['POST'])
def analyze_mood():
    """
    Analyzes mood from text or simulated voice input.
    Body: { text: "I'm feeling tired today", user_id: "user1" }
    """
    data    = request.json or {}
    text    = data.get('text', '')
    user_id = data.get('user_id', 'user1')

    result = mood_analyzer.analyze(text, user_id)

    # Update harmonizer with new mood reading
    user_harmonizer.update_mood(user_id, result['mood'], result['score'])

    # Auto-adjust environment based on mood
    env_changes = mood_analyzer.get_environment_adjustments(result['mood'])
    simulator.apply_mood_adjustments(env_changes)

    # Store in adaptive memory
    adaptive_memory.record_mood_event(user_id, result['mood'], datetime.now())

    return jsonify({**result, 'environment_changes': env_changes})

@app.route('/api/mood/history/<user_id>')
def mood_history(user_id):
    return jsonify(mood_analyzer.get_history(user_id))

# ─── Multi-User Harmonizer ────────────────────────────────────
@app.route('/api/users/harmonize')
def harmonize_users():
    """Balance environment preferences across all active users."""
    result = user_harmonizer.harmonize()
    if result.get('consensus'):
        simulator.apply_recommendations(result['consensus'])
    return jsonify(result)

@app.route('/api/users/add', methods=['POST'])
def add_user():
    data = request.json or {}
    user_harmonizer.add_user(data.get('user_id'), data.get('name'), data.get('preferences', {}))
    return jsonify({'success': True, 'users': user_harmonizer.get_users()})

# ─── Adaptive Memory ──────────────────────────────────────────
@app.route('/api/memory/patterns')
def get_patterns():
    return jsonify(adaptive_memory.get_patterns())

@app.route('/api/memory/record', methods=['POST'])
def record_preference():
    data = request.json or {}
    adaptive_memory.record_preference(
        data.get('user_id'), data.get('setting'), data.get('value'), data.get('context', {})
    )
    return jsonify({'success': True})

# ─── Voice Assistant ──────────────────────────────────────────
@app.route('/api/voice/command', methods=['POST'])
def voice_command():
    """
    Process voice command (text input simulating speech recognition).
    Body: { command: "turn off the lights", user_id: "user1" }
    For real speech: call voice_assistant.listen() before this endpoint.
    """
    data    = request.json or {}
    command = data.get('command', '')
    user_id = data.get('user_id', 'user1')

    result  = voice_assistant.process_command(command, simulator, mood_analyzer, user_id)
    return jsonify(result)

@app.route('/api/voice/speak', methods=['POST'])
def text_to_speech():
    """Convert text to speech (uses pyttsx3 offline TTS)."""
    data = request.json or {}
    text = data.get('text', '')
    voice_assistant.speak(text)
    return jsonify({'success': True, 'text': text})

# ─── Simulation Control ───────────────────────────────────────
@app.route('/api/simulation/state')
def sim_state():
    return jsonify(simulator.get_state())

@app.route('/api/simulation/tick')
def sim_tick():
    """Advance simulation by one time step (5 minutes)."""
    simulator.tick()
    return jsonify(simulator.get_state())

@app.route('/api/simulation/appliance', methods=['POST'])
def control_appliance():
    """
    Manual override for appliance control.
    Body: { appliance: "ac", state: "on", value: 22 }
    In hardware mode: forwards command to real device.
    """
    data = request.json or {}
    result = simulator.control_appliance(
        data.get('appliance'), data.get('state'), data.get('value')
    )
    adaptive_memory.record_override(
        data.get('user_id', 'user1'), data.get('appliance'), data.get('value')
    )
    return jsonify(result)

@app.route('/api/simulation/reset')
def reset_simulation():
    simulator.reset()
    return jsonify({'success': True, 'state': simulator.get_state()})

# ─── Hardware Integration (Modular / Future) ──────────────────
@app.route('/api/hardware/connect', methods=['POST'])
def connect_hardware():
    """
    HARDWARE MODULE PLACEHOLDER
    When Raspberry Pi or smart hub is connected:
      POST { device_type: "raspberry_pi", host: "192.168.1.x", port: 8080 }
    This endpoint will switch the system from simulation to live mode.
    """
    data = request.json or {}
    # TODO: Initialize hardware adapter
    # from modules.hardware_adapter import HardwareAdapter
    # global hardware = HardwareAdapter(data['host'], data['port'])
    return jsonify({
        'message': 'Hardware integration ready - connect your device',
        'instructions': {
            'raspberry_pi': 'Flash smart_home/hardware/rpi_agent.py to your Pi',
            'smart_plugs':  'Add TUYA_API_KEY to .env and uncomment tuya module',
            'alexa':        'Deploy skill via alexa_skill/ folder to AWS Lambda',
            'google_home':  'Use google_home/actions.json with DialogFlow'
        }
    })

@app.route('/api/sensors/update', methods=['POST'])
def update_sensors():
    """
    Receive real sensor data (temperature, noise, light, occupancy).
    When hardware is connected, sensors POST here every 30 seconds.
    Body: { temperature: 24.5, noise: 35, light: 200, occupancy: true }
    """
    data = request.json or {}
    simulator.update_from_sensors(data)
    # Trigger AI re-analysis when sensor data arrives
    sleep_score = sleep_optimizer.get_current_score(data)
    if sleep_score['score'] < 60:
        recs = sleep_optimizer.optimize(data)
        simulator.apply_recommendations(recs.get('recommendations', {}))
    return jsonify({'received': True, 'sleep_score': sleep_score})

# ─── Alexa / Google Home Webhooks ─────────────────────────────
@app.route('/api/alexa/intent', methods=['POST'])
def alexa_intent():
    """
    Alexa Smart Home Skill webhook.
    Deploy your Alexa skill to point to: https://your-domain/api/alexa/intent
    """
    data   = request.json or {}
    intent = data.get('request', {}).get('intent', {}).get('name', '')
    slots  = data.get('request', {}).get('intent', {}).get('slots', {})
    result = voice_assistant.handle_alexa_intent(intent, slots, simulator)
    return jsonify(result)

@app.route('/api/google/fulfillment', methods=['POST'])
def google_fulfillment():
    """
    Google Home Actions fulfillment endpoint.
    Connect via Google Actions Console → Fulfillment → Webhook URL
    """
    data   = request.json or {}
    intent = data.get('queryResult', {}).get('intent', {}).get('displayName', '')
    params = data.get('queryResult', {}).get('parameters', {})
    result = voice_assistant.handle_google_intent(intent, params, simulator)
    return jsonify(result)

if __name__ == '__main__':
    print("\n" + "═"*60)
    print("  🏠 AI Smart Home Intelligence System")
    print("  Mode: Software Simulation (Hardware-Ready)")
    print("  Dashboard: http://localhost:5000")
    print("═"*60 + "\n")
    app.run(debug=True, port=5000, threaded=True)
