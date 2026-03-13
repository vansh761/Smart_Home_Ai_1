"""
Energy Optimizer Module
-----------------------
Predicts energy consumption using time-of-day patterns and
optimizes appliance scheduling to minimize cost/usage.
Uses a simple regression model trained on simulated data.
"""

import math
import random
from datetime import datetime, timedelta


class EnergyOptimizer:
    """
    AI model for energy prediction and appliance scheduling.
    Model: Sinusoidal pattern + noise (mimics real household data).
    Replace with sklearn LinearRegression or LSTM for real data.
    """

    def __init__(self):
        # Learned weights (would come from training in production)
        self._weights = {
            'morning_peak':  0.85,   # 6-9 AM peak
            'evening_peak':  1.0,    # 5-9 PM peak
            'night_low':     0.3,    # 11 PM - 5 AM low
            'base_kwh':      0.8,    # Baseline kWh per hour
        }
        self._history = self._generate_history()
        self._appliance_schedules = {}

    # ── Prediction ───────────────────────────────────────────
    def predict_24h(self, start_hour: int = 0) -> list:
        """
        Predict hourly energy usage for next 24 hours.
        Returns list of { hour, kwh, cost, peak } dicts.
        """
        predictions = []
        for i in range(24):
            hour = (start_hour + i) % 24
            kwh  = self._predict_hour(hour)
            predictions.append({
                'hour':    hour,
                'label':   f'{hour:02d}:00',
                'kwh':     round(kwh, 3),
                'cost':    round(kwh * self._get_rate(hour), 4),
                'peak':    self._is_peak(hour),
                'index':   i
            })
        return predictions

    def _predict_hour(self, hour: int) -> float:
        """Sinusoidal model with peaks at morning and evening."""
        # Morning ramp (6-9 AM)
        morning = max(0, math.sin(math.pi * (hour - 4) / 6)) * self._weights['morning_peak']
        # Evening ramp (17-21)
        evening = max(0, math.sin(math.pi * (hour - 15) / 8)) * self._weights['evening_peak']
        base    = self._weights['base_kwh']
        noise   = random.gauss(0, 0.05)
        return max(0.1, base + morning + evening + noise)

    def _get_rate(self, hour: int) -> float:
        """Time-of-use electricity rate ($/kWh)."""
        if self._is_peak(hour):
            return 0.28   # Peak rate
        elif 23 <= hour or hour < 7:
            return 0.10   # Off-peak (night)
        return 0.18       # Standard

    def _is_peak(self, hour: int) -> bool:
        return (7 <= hour <= 9) or (17 <= hour <= 21)

    # ── Schedule Optimization ────────────────────────────────
    def optimize_schedule(self, predictions: list) -> dict:
        """
        Shift deferrable appliances (dishwasher, laundry, EV charger)
        to off-peak hours to minimize cost.
        """
        off_peak_hours = [p['hour'] for p in predictions if not p['peak'] and p['hour'] >= 21]
        if not off_peak_hours:
            off_peak_hours = [23, 0, 1, 2, 3]

        schedule = {
            'dishwasher': {
                'recommended_hour': off_peak_hours[0] if off_peak_hours else 23,
                'savings':          round(random.uniform(0.10, 0.35), 2),
                'reason':           'Off-peak electricity rate'
            },
            'washing_machine': {
                'recommended_hour': off_peak_hours[1] if len(off_peak_hours) > 1 else 22,
                'savings':          round(random.uniform(0.20, 0.50), 2),
                'reason':           'Lowest rate period'
            },
            'ev_charger': {
                'recommended_hour': 2,
                'savings':          round(random.uniform(1.50, 3.00), 2),
                'reason':           'Super off-peak rate (2-5 AM)'
            }
        }

        total_savings = sum(s['savings'] for s in schedule.values())
        schedule['_meta'] = {
            'total_daily_savings': round(total_savings, 2),
            'peak_avoidance_hours': off_peak_hours[:4]
        }
        return schedule

    # ── Stats & History ──────────────────────────────────────
    def get_current_stats(self) -> dict:
        """Current energy snapshot for dashboard."""
        now      = datetime.now()
        hour     = now.hour
        current  = self._predict_hour(hour)
        daily    = sum(self._predict_hour(h) for h in range(24))
        return {
            'current_kwh':   round(current, 3),
            'daily_total':   round(daily, 2),
            'daily_cost':    round(daily * 0.18, 2),
            'peak_status':   'peak' if self._is_peak(hour) else 'off-peak',
            'rate':          self._get_rate(hour),
            'co2_kg':        round(daily * 0.233, 2),   # avg grid emission factor
            'efficiency':    round(random.uniform(72, 92), 1)
        }

    def get_history(self) -> list:
        """Return 7-day energy history."""
        return self._history

    def _generate_history(self) -> list:
        """Simulate 7 days of hourly data."""
        history = []
        base    = datetime.now() - timedelta(days=7)
        for day in range(7):
            day_kwh = 0
            for h in range(24):
                kwh = self._predict_hour(h)
                day_kwh += kwh
            history.append({
                'date':      (base + timedelta(days=day)).strftime('%a %m/%d'),
                'total_kwh': round(day_kwh, 2),
                'cost':      round(day_kwh * 0.18, 2),
                'peak_pct':  round(random.uniform(30, 55), 1)
            })
        return history
