# src/recommend.py
import random

FALLBACK_MOVE = {
    "id": "hold_groove",
    "name": "Hold / Groove",
    "style": ["open"],
    "beats": 1,
    "tempo_bpm_min": 40,
    "tempo_bpm_max": 220,
    "energy": "neutral",
}

def _candidates(eligible, beats_left, avoid_last_id=None, allow_repeat=True):
    c = [m for m in eligible if m.get("beats", 1) <= beats_left]
    if not allow_repeat and avoid_last_id is not None:
        c = [m for m in c if m["id"] != avoid_last_id]
    # prefer larger multi-beat first
    c.sort(key=lambda m: m.get("beats", 1), reverse=True)
    return c

def fill_phrase(eligible_moves, beats_in_phrase=8, avoid_last_id=None):
    plan, total = [], 0
    attempts = 0
    allow_repeat = False  # start strict, relax if needed
    while total < beats_in_phrase and attempts < 200:
        beats_left = beats_in_phrase - total
        cand = _candidates(eligible_moves, beats_left, avoid_last_id, allow_repeat=allow_repeat)
        if not cand:
            if not allow_repeat:
                # relax no-repeat constraint
                allow_repeat = True
                continue
            # still nothing? pad with holds
            plan.append(FALLBACK_MOVE)
            total += 1
            avoid_last_id = FALLBACK_MOVE["id"]
            attempts += 1
            continue
        pick = random.choice(cand[:min(3, len(cand))])
        plan.append(pick)
        total += pick.get("beats", 1)
        avoid_last_id = pick["id"]
        attempts += 1
    return plan if total == beats_in_phrase else None

def recommend_sequence(beat_times, bpm, moves, phrases=4):
    eligible = [m for m in moves if m["tempo_bpm_min"] <= bpm <= m["tempo_bpm_max"]]
    # ensure we always have a fallback
    eligible = eligible + [FALLBACK_MOVE]

    sequence = []
    last_id = None
    for _ in range(phrases):
        phrase_moves = fill_phrase(eligible, 8, avoid_last_id=last_id)
        if not phrase_moves:
            phrase_moves = [FALLBACK_MOVE] * 8
        sequence.append(phrase_moves)
        last_id = phrase_moves[-1]["id"]

    # Build flat timeline, but stop if we run out of beat boundaries
    flat = []
    beat_idx = 0
    n_bounds = len(beat_times)  # boundaries; valid end boundary requires index < n_bounds
    for phrase in sequence:
        for move in phrase:
            beats = move.get("beats", 1)
            start_idx = beat_idx
            end_idx = beat_idx + beats
            # Need an end boundary: end_idx < n_bounds
            if end_idx >= n_bounds:
                return flat  # stop cleanly at end of known beats
            start_time = float(beat_times[start_idx])
            end_time = float(beat_times[end_idx])
            duration = end_time - start_time
            flat.append({
                "move_id": move["id"],
                "name": move["name"],
                "beats": beats,
                "start_beat_index": start_idx,
                "end_beat_index": end_idx,  # boundary index
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
            })
            beat_idx = end_idx
    return flat
