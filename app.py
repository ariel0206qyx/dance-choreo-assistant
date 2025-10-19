# app.py  (add/modify imports)
import streamlit as st
from src.audio import analyze_audio, section_bpms
from src.library import load_library
from src.recommend import recommend_sequence

st.title("Choreo Ideation Assistant (MVP)")

audio_file = st.file_uploader("Upload an audio file", type=["mp3","wav","m4a"])
if audio_file:
    with open("tmp_audio", "wb") as f:
        f.write(audio_file.read())
    st.audio("tmp_audio")

    analysis = analyze_audio("tmp_audio")
    tempo = analysis["tempo"]
    beat_times = analysis["beat_times"]

    st.subheader("Tempo")
    st.write(f"**Estimated global tempo:** {tempo:.1f} BPM")

    # Section speeds (8-count by default)
    sections = section_bpms(beat_times, beats_per_section=8, agg="median")
    # after sections = section_bpms(...)

    if sections:
        st.write("**Section tempos (per 8-count):**")
        # let you choose how many sections to display
        max_to_show = st.number_input(
            "How many sections to show?",
            min_value=1,
            max_value=len(sections),
            value=min(12, len(sections)),
            step=1,
        )
        for s in sections[:max_to_show]:
            st.write(
                f"Section {s['section_index']}: {s['bpm']:.1f} BPM — "
                f"beats {s['start_beat']+1}–{s['end_beat']} "
                f"({s['start_time']:.2f}s → {s['end_time']:.2f}s, {s['duration']:.2f}s)"
            )


    moves = load_library()

    total_complete_beats = max(0, len(beat_times) - 1)
    auto_phrases = max(1, total_complete_beats // 8)

    max_phrases = st.slider("How many 8-count phrases to generate?",
                            min_value=1, max_value=auto_phrases, value=min(8, auto_phrases))

    plan = recommend_sequence(beat_times, tempo, moves, phrases=max_phrases)

    if plan:
        st.subheader("Suggested Moves")
        for step in plan:
            # only display if we have a reasonable duration
            if step["duration"] is None:
                continue
            st.write(
                f"{step['name']} — beats {step['start_beat_index']+1}-{step['end_beat_index']} "
                f"({step['start_time']:.2f}s → {step['end_time']:.2f}s, {step['duration']:.2f}s)"
            )
