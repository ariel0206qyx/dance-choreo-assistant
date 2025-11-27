import librosa
import numpy as np

def instant_bpms(beat_times):
    """BPM between consecutive beats."""
    beat_times = np.asarray(beat_times, dtype=float)
    if len(beat_times) < 2:
        return []
    deltas = np.diff(beat_times)               # seconds per beat
    with np.errstate(divide="ignore", invalid="ignore"):
        bpms = 60.0 / deltas
    return bpms.tolist()

def section_bpms(beat_times, beats_per_section=8, agg="median"):
    """
    Compute a BPM per section (e.g., per 8-count) using median or mean of instant BPMs inside that section.
    Returns: list of dicts with section_index, start_beat, end_beat (exclusive), bpm.
    """
    ibpms = np.asarray(instant_bpms(beat_times), dtype=float)  # length: len(beat_times)-1
    sections = []
    n_beats = len(beat_times)
    sec_idx = 0
    for start in range(0, n_beats-1, beats_per_section):
        end = min(start + beats_per_section, n_beats-1)  # -1 because ibpms is between beats
        if end <= start:
            break
        window = ibpms[start:end]
        if window.size == 0:
            continue
        bpm = float(np.median(window) if agg == "median" else np.mean(window))
        sections.append({
            "section_index": sec_idx,
            "start_beat": start,     # inclusive
            "end_beat": end,         # exclusive
            "bpm": bpm,
            "start_time": float(beat_times[start]),
            "end_time": float(beat_times[end]),
            "duration": float(beat_times[end] - beat_times[start]),
        })
        sec_idx += 1
    return sections


def analyze_audio(path):
    y, sr = librosa.load(path, sr=None, mono=True)
    # Onset strength → more robust beat tracking
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env, units='frames')
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Map beats to 4/4 counts: 1..4 repeating (v1 heuristic)
    counts = (np.arange(len(beat_times)) % 4) + 1

    return {
        "tempo": float(tempo),
        "beat_times": beat_times.tolist(),
        "counts": counts.tolist()
    }
