import random
from collections import defaultdict, deque

# Simple fallback move if nothing fits (rarely used but keeps things safe)
FALLBACK_MOVE = {
    "id": "hold_groove",
    "name": "Hold / Groove",
    "style": ["open"],
    "beats": 1,
    "tempo_bpm_min": 40,
    "tempo_bpm_max": 220,
    "energy": "neutral",
    "difficulty": "easy",
    "tags": ["fill", "reset"],
    "notes": "Small bounce or vibe; use to pad phrases."
}


def _candidate_score(move, usage_counts):
    """
    Lower usage count = better.
    For ties, prefer longer moves (more beats) to avoid a million 1-beat fillers.
    """
    beats = move.get("beats", 1)
    return (usage_counts[move["id"]], -beats)


def _get_candidates(eligible, beats_left, usage_counts, recent_ids, allow_recent):
    """
    Filter and sort candidates:
      - must fit in remaining beats
      - if allow_recent is False: avoid ids in recent_ids
      - sort by (usage_count, -beats)
    """
    cands = [
        m for m in eligible
        if m.get("beats", 1) <= beats_left
    ]
    if not allow_recent:
        cands = [m for m in cands if m["id"] not in recent_ids]

    if not cands:
        return []

    cands.sort(key=lambda m: _candidate_score(m, usage_counts))
    return cands


def fill_phrase(eligible_moves, beats_in_phrase, usage_counts, recent_ids, recent_window=3):
    """
    Build one 8-count phrase, balancing:
      - fitting exactly beats_in_phrase
      - avoiding immediate repeats (recent_ids)
      - using low-usage moves first
    """
    plan = []
    total = 0
    attempts = 0

    # recent_ids is a deque shared across the whole sequence
    # so variety is global, not just inside one phrase
    while total < beats_in_phrase and attempts < 200:
        beats_left = beats_in_phrase - total

        # 1) Try to avoid very recent moves
        cands = _get_candidates(
            eligible_moves,
            beats_left,
            usage_counts,
            recent_ids,
            allow_recent=False
        )

        # 2) If nothing fits, allow recent ones too
        if not cands:
            cands = _get_candidates(
                eligible_moves,
                beats_left,
                usage_counts,
                recent_ids,
                allow_recent=True
            )

        # 3) Still nothing? Use fallback 1-beat move
        if not cands:
            move = FALLBACK_MOVE
        else:
            # Prefer among the best few candidates for some randomness
            top_k = min(3, len(cands))
            move = random.choice(cands[:top_k])

        beats = move.get("beats", 1)
        plan.append(move)
        total += beats

        move_id = move["id"]
        usage_counts[move_id] += 1
        recent_ids.append(move_id)
        # bound the window size
        while len(recent_ids) > recent_window:
            recent_ids.popleft()

        attempts += 1

    # If we ended up over/under, just return what we have (caller can decide)
    return plan


def recommend_sequence(beat_times, bpm, moves, phrases=4):
    """
    Build a flat list of moves across multiple 8-count phrases,
    trying to:
      - respect tempo
      - avoid repeating the same moves
      - stop cleanly when we run out of beats in beat_times
    """
    # Filter moves by tempo
    eligible = [m for m in moves if m["tempo_bpm_min"] <= bpm <= m["tempo_bpm_max"]]
    # Ensure we always have at least the fallback move
    eligible = eligible + [FALLBACK_MOVE]

    usage_counts = defaultdict(int)
    recent_ids = deque()  # global recent-move memory

    sequence_phrases = []
    for _ in range(phrases):
        phrase_moves = fill_phrase(eligible, beats_in_phrase=8,
                                   usage_counts=usage_counts,
                                   recent_ids=recent_ids)
        sequence_phrases.append(phrase_moves)

    # ---- flatten into a timeline with times ----
    flat = []
    beat_idx = 0
    n_bounds = len(beat_times)  # we need end_idx < n_bounds

    for phrase in sequence_phrases:
        for move in phrase:
            beats = move.get("beats", 1)
            start_idx = beat_idx
            end_idx = beat_idx + beats

            # no more beat boundaries -> stop
            if end_idx >= n_bounds:
                return flat

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
