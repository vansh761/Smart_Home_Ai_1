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
        self._users = {}
        self._add_defaults()

    def _add_defaults(self):
        self._users['user1'] = {
            'name':     'Alice',
            'mood':     'neutral',
            'score':    60,
            'active':   True,
            'priority': 1.0,
            'prefs':    {'temp_pref': 21, 'light_pref': 70}
        }
        self._users['user2'] = {
            'name':     'Bob',
            'mood':     'neutral',
            'score':    60,
            'active':   False,
            'priority': 1.0,
            'prefs':    {'temp_pref': 20, 'light_pref': 60}
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
            self._users[user_id] = {'name': user_id, 'active': True, 'priority': 1.0, 'prefs': {}}
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
                'consensus': user.get('prefs', {}),
                'message':   f"Single user ({user['name']}) — using individual preferences",
                'conflicts': []
            }

        # Weight by priority; lower mood score = higher priority (comfort the distressed)
        weights  = {}
        total_wt = 0
        for uid, u in active.items():
            mood_wt      = max(0.5, (100 - u.get('score', 60)) / 100)
            pri          = u.get('priority', 1.0)
            weights[uid] = mood_wt * pri
            total_wt    += weights[uid]

        temp_weighted = sum(
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
            'user_weights': {uid: round(w / total_wt, 2) for uid, w in weights.items()},
            'conflicts':    conflicts,
            'message':      f"Harmonized settings for {len(active)} users"
        }

    def _detect_conflicts(self, active: dict) -> list:
        conflicts = []
        users = list(active.items())
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

