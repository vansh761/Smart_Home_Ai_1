"""
Home Simulator Module
---------------------
Simulates a smart home environment (appliances, sensors, room conditions).
This is the software-only layer — replace with real hardware adapters
by inheriting from HomeSimulator and overriding control methods.
"""

import random
import math
from datetime import datetime


class HomeSimulator:
    """
    Simulates room conditions and appliance states.
    Evolves over time via tick() to mimic real-world changes.

    HARDWARE INTEGRATION:
      Create HardwareAdapter(HomeSimulator) that overrides:
        - control_appliance() → send MQTT/HTTP command to real device
        - get_state() → read from real sensors
        - tick() → no-op (real sensors provide updates)
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Initialize default home state."""
        self._state = {
            # Room conditions
            'temperature':  22.0,    # °C
            'humidity':     55.0,    # %
            'noise_level':  35.0,    # dB
            'light_level':  70.0,    # % brightness
            'co2_level':    450,     # ppm
            'air_quality':  85,      # 0-100 (higher = better)

            # Appliances
            'ac':           {'state': 'off', 'target': 22, 'mode': 'cool'},
            'fan':          {'state': 'off', 'speed': 'low'},
            'lights':       {'state': 'on',  'brightness': 70, 'color': 'daylight'},
            'heater':       {'state': 'off'},
            'white_noise':  {'state': 'off'},
            'music':        {'state': 'off', 'genre': 'none'},

            # Home state
            'occupancy':    True,
            'sleep_mode':   False,
            'hour':         datetime.now().hour,
            'tick_count':   0,

            # Notifications
            'alerts':       []
        }
        self._tick = 0

    def get_state(self) -> dict:
        """Return current simulated state."""
        return dict(self._state)

    def tick(self):
        """
        Advance simulation by ~5 minutes.
        Updates temperature, noise, and light based on appliance states and time.
        """
        self._tick += 1
        self._state['tick_count'] = self._tick
        hour = (datetime.now().hour + self._tick // 12) % 24
        self._state['hour'] = hour

        # Temperature drift toward ambient (24°C outside baseline)
        ambient   = 24 + 4 * math.sin(math.pi * (hour - 14) / 12)
        temp      = self._state['temperature']
        ac        = self._state['ac']
        heater    = self._state['heater']

        if ac['state'] == 'on':
            target  = ac.get('target', 22)
            temp   += (target - temp) * 0.15      # AC pulls toward target
        elif heater['state'] == 'on':
            temp   += 0.3
        else:
            temp   += (ambient - temp) * 0.05    # Passive drift toward ambient

        self._state['temperature'] = round(min(35, max(10, temp + random.gauss(0, 0.1))), 1)

        # Noise floor varies by time of day
        base_noise = 20 if (23 <= hour or hour < 6) else 40
        self._state['noise_level'] = round(base_noise + random.gauss(0, 3), 1)

        # Light follows natural day/night if in auto mode
        if not self._state['sleep_mode']:
            natural = max(10, 100 * math.sin(math.pi * (hour - 6) / 14)) if 6 <= hour <= 20 else 10
            current = self._state['light_level']
            self._state['light_level'] = round(current + (natural - current) * 0.1, 1)

        # CO2 builds with occupancy
        if self._state['occupancy']:
            self._state['co2_level'] = min(1500, self._state['co2_level'] + random.randint(1, 5))
        else:
            self._state['co2_level'] = max(400, self._state['co2_level'] - 3)

        self._check_alerts()

    def control_appliance(self, appliance: str, state: str, value=None) -> dict:
        """
        Control a simulated appliance.
        In hardware mode: override this to send real commands.
        """
        if appliance not in self._state and appliance not in ['ac', 'fan', 'lights', 'heater', 'white_noise', 'music']:
            return {'success': False, 'error': f'Unknown appliance: {appliance}'}

        target = self._state.get(appliance, {})

        if isinstance(target, dict):
            target['state'] = state
            if value is not None:
                if appliance == 'ac':
                    target['target'] = value
                elif appliance == 'lights':
                    target['brightness'] = value
                    self._state['light_level'] = float(value)
                elif appliance == 'fan':
                    target['speed'] = value
        else:
            self._state[appliance] = state

        return {
            'success':   True,
            'appliance': appliance,
            'new_state': self._state.get(appliance),
            'value':     value
        }

    def apply_recommendations(self, recs: dict):
        """Apply a dict of recommended settings from AI modules."""
        if 'temperature' in recs:
            target = recs['temperature']
            self._state['ac']['state']  = 'on'
            self._state['ac']['target'] = target
        if 'lights' in recs:
            self._state['lights']['brightness'] = recs['lights']
            self._state['light_level']           = float(recs['lights'])
            self._state['lights']['state']       = 'on' if recs['lights'] > 0 else 'off'
        if 'fan' in recs:
            self._state['fan']['state'] = recs['fan']
        if 'white_noise' in recs:
            self._state['white_noise']['state'] = recs['white_noise']
        if 'sleep_mode' in recs:
            self._state['sleep_mode'] = recs['sleep_mode']
        if 'music' in recs:
            self._state['music']['state'] = 'on' if recs['music'] != 'off' else 'off'
            self._state['music']['genre'] = recs.get('music', 'none')

    def apply_mood_adjustments(self, env: dict):
        """Apply mood-driven environment changes."""
        self.apply_recommendations({
            'temperature': env.get('temperature'),
            'lights':      env.get('lights'),
            'fan':         env.get('fan', 'off'),
            'music':       env.get('music', 'off')
        })
        if 'light_color' in env:
            self._state['lights']['color'] = env['light_color']

    def update_from_sensors(self, sensor_data: dict):
        """
        Update state from real sensor readings.
        Called when physical sensors POST data to /api/sensors/update.
        """
        for key in ['temperature', 'noise_level', 'light_level', 'humidity', 'co2_level']:
            if key in sensor_data:
                self._state[key] = sensor_data[key]
        if 'occupancy' in sensor_data:
            self._state['occupancy'] = sensor_data['occupancy']

    def _check_alerts(self):
        """Generate alerts for out-of-range conditions."""
        alerts = []
        if self._state['temperature'] > 28:
            alerts.append({'type': 'warning', 'msg': 'High temperature detected', 'action': 'Enable AC'})
        if self._state['co2_level'] > 1000:
            alerts.append({'type': 'warning', 'msg': 'CO₂ levels elevated', 'action': 'Open windows or ventilate'})
        if self._state['noise_level'] > 65:
            alerts.append({'type': 'info', 'msg': 'Noise levels above comfort threshold'})
        self._state['alerts'] = alerts
