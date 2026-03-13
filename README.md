# 🏠 NEXUS — AI Smart Home Intelligence System
### Hackathon-Ready · Software-First · Hardware-Modular

---

## Quick Start (Software-Only, 2 Minutes)

```bash
# 1. Install dependencies
pip install flask flask-cors pyttsx3 SpeechRecognition

# 2. Run
python app.py

# 3. Open dashboard
# http://localhost:5000
```

No hardware required. Everything simulates in software.

---

## Architecture

```
smart_home/
├── app.py                    ← Flask backend + all API routes
├── requirements.txt
├── templates/
│   └── index.html            ← Full dashboard (Chart.js, real-time)
└── modules/
    ├── energy_optimizer.py   ← Energy prediction + schedule optimization
    ├── sleep_optimizer.py    ← Sleep quality scoring + recommendations
    ├── mood_analyzer.py      ← Sentiment analysis + environment mapping
    ├── adaptive_memory.py    ← User habit learning + pattern detection
    │                           (also contains UserHarmonizer + VoiceAssistant)
    ├── voice_assistant.py    ← Re-export shim
    ├── user_harmonizer.py    ← Re-export shim
    └── simulation.py         ← Full home environment simulator
```

---

## AI Modules

| Module | Model | Input | Output |
|--------|-------|-------|--------|
| EnergyOptimizer | Sinusoidal regression | Hour of day | kWh predictions, schedule |
| SleepOptimizer | Rule-based + weighted scoring | Temp, noise, light | Score 0-100, recommendations |
| MoodAnalyzer | Keyword + lexicon sentiment | Text (voice transcript) | Mood label, environment changes |
| AdaptiveMemory | Frequency analysis | User interactions | Patterns, proactive suggestions |
| UserHarmonizer | Weighted averaging | Multi-user moods | Consensus environment |
| VoiceAssistant | Regex pattern matching | Command text | Action + TTS response |

---

## API Reference

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/status | Full system state |

### Energy
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/energy/predict | 24h predictions |
| GET | /api/energy/history | 7-day history |

### Sleep
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/sleep/optimize | Optimize conditions |
| GET | /api/sleep/score | Current score |

### Mood
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/mood/analyze | Body: `{"text": "...", "user_id": "..."}` |
| GET | /api/mood/history/<user_id> | Mood history |

### Voice
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/voice/command | Body: `{"command": "...", "user_id": "..."}` |
| POST | /api/voice/speak | TTS output |

### Simulation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/simulation/state | Current state |
| GET | /api/simulation/tick | Advance 5 minutes |
| POST | /api/simulation/appliance | Control appliance |
| GET | /api/simulation/reset | Reset to defaults |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users/harmonize | Balance preferences |
| POST | /api/users/add | Add user |

---

## Voice Commands

Say these into the dashboard or POST to `/api/voice/command`:

```
"turn on the lights"       → lights on
"turn off the lights"      → lights off  
"set temperature to 20"    → AC target 20°C
"dim the lights"           → 30% brightness
"sleep mode"               → 18°C, dim lights, fan off
"good morning"             → 22°C, full lights
"energy report"            → daily stats
"I feel stressed"          → calm environment
"I feel happy"             → energetic environment
"play ambient music"       → music mode
```

---

## Hardware Integration

### Raspberry Pi
```bash
# On your Pi, install and run the agent:
pip install flask requests gpiozero
python hardware/rpi_agent.py --host 0.0.0.0 --port 8080

# Then connect from the main system:
POST /api/hardware/connect
{"device_type": "raspberry_pi", "host": "192.168.1.x", "port": 8080}
```

### Smart Plugs (Tuya / TP-Link)
```bash
pip install tinytuya
# Add to .env: TUYA_API_KEY, TUYA_API_SECRET, TUYA_REGION
# Uncomment tuya module in modules/hardware_adapter.py
```

### Real Sensors → POST to:
```
POST /api/sensors/update
{
  "temperature": 24.5,
  "noise_level": 38,
  "light_level": 200,
  "humidity": 55,
  "occupancy": true
}
```
The AI will auto-optimize based on real readings.

### Alexa Integration
1. Create Alexa Smart Home skill in developer.amazon.com
2. Set fulfillment endpoint to `https://your-domain/api/alexa/intent`
3. Map intents: TurnOnIntent, TurnOffIntent, SetTempIntent, SleepModeIntent

### Google Home
1. Create Action in console.actions.google.com
2. Set webhook to `https://your-domain/api/google/fulfillment`
3. Map DisplayName intents to your commands

---

## Upgrading the AI Models

### Better Mood Detection
```python
# Replace keyword matching in mood_analyzer.py with:
from transformers import pipeline
classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
result = classifier(text)
```

### Real Energy Forecasting
```python
# Replace sinusoidal model with:
from sklearn.linear_model import LinearRegression
# Train on: pandas_profiling + real smart meter CSV data
```

### Voice Recognition (Offline)
```bash
pip install openai-whisper
# Replace Google STT in voice_assistant.py with:
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.wav")
```

---

## Environment Variables (.env)

```bash
FLASK_ENV=development
FLASK_PORT=5000
TUYA_API_KEY=your_key          # Optional: Tuya smart plugs
TUYA_API_SECRET=your_secret    # Optional: Tuya smart plugs
ALEXA_SKILL_ID=your_skill_id   # Optional: Alexa integration
GOOGLE_PROJECT_ID=your_id      # Optional: Google Home
```

---

## Hackathon Tips

1. **Demo the mood detection**: Type "I feel stressed" → watch environment change
2. **Show harmonization**: Toggle User 2 active → click Harmonize
3. **Energy savings**: Hit "⚡ Refresh Predictions" → show off-peak scheduling
4. **Voice quick commands**: Use the quick-command buttons in the dashboard
5. **Tick simulation**: Click "TICK +5m" to show environment evolving over time

---

Built for hackathons. Extend, fork, and ship it. 🚀
