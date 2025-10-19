# src/library.py
import json

def load_library(path="motion_library.json"):
    with open(path) as f:
        return json.load(f)

def filter_by_tempo(moves, bpm):
    return [m for m in moves if m["tempo_bpm_min"] <= bpm <= m["tempo_bpm_max"]]
