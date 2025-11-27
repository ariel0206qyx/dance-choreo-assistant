import os
import streamlit as st

from src.audio import analyze_audio, section_bpms
from src.library import load_library
from src.recommend import recommend_sequence


st.title("Choreo Ideation Assistant (MVP)")

audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if audio_file:
    TMP_PATH = "tmp_audio"

    # Save uploaded audio to temp file
    with open(TMP_PATH, "wb") as f:
        f.write(audio_file.read())
    st.audio(TMP_PATH)

    # ---- Audio analysis ----
    analysis = analyze_audio(TMP_PATH)
    tempo = analysis["tempo"]
    beat_times = analysis["beat_times"]

    st.subheader("Tempo")
    st.write(f"**Estimated global tempo:** {tempo:.1f} BPM")

    # estimate song duration from last beat time
    approx_duration = float(beat_times[-1]) if len(beat_times) > 0 else 0.0

    # Section speeds (8-count by default)
    sections = section_bpms(beat_times, beats_per_section=8, agg="median")

    # --- Time scrub control (for highlighting) ---
    current_time = None
    if approx_duration > 0:
        current_time = st.slider(
            "Scrub time (seconds, approx based on beats)",
            min_value=0.0,
            max_value=approx_duration,
            value=0.0,
            step=0.1,
        )

    # ---- Show section tempos, highlighting current section ----
    active_section_idx = None
    if current_time is not None and sections:
        for s in sections:
            if s["start_time"] <= current_time <= s["end_time"]:
                active_section_idx = s["section_index"]
                break

    if sections:
        st.write("**Section tempos (per 8-count):**")
        max_to_show = st.number_input(
            "How many sections to show?",
            min_value=1,
            max_value=len(sections),
            value=min(12, len(sections)),
            step=1,
        )

        for s in sections[:max_to_show]:
            text = (
                f"Section {s['section_index']}: {s['bpm']:.1f} BPM — "
                f"beats {s['start_beat']+1}–{s['end_beat']} "
                f"({s['start_time']:.2f}s → {s['end_time']:.2f}s, {s['duration']:.2f}s)"
            )

            if active_section_idx is not None and s["section_index"] == active_section_idx:
                # highlight active section
                st.markdown(
                    f"<div style='background-color:#FFF3CD;padding:4px 8px;border-radius:4px;'>"
                    f"▶ {text}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.write(text)

    # ---- Load motion library ----
    try:
        moves = load_library()
    except Exception as e:
        st.error(f"Failed to load motion library: {e}")
        moves = []

    moves_by_id = {m["id"]: m for m in moves}

    if not moves:
        st.warning("Your motion library is empty. Add entries to motion_library.json to see suggestions.")
    else:
        total_complete_beats = max(0, len(beat_times) - 1)
        auto_phrases = max(1, total_complete_beats // 8) if total_complete_beats > 0 else 0

        if auto_phrases == 0:
            st.info("Not enough detected beats to generate phrases yet.")
        else:
            max_phrases = st.slider(
                "How many 8-count phrases to generate?",
                min_value=1,
                max_value=auto_phrases,
                value=min(8, auto_phrases),
            )

            plan = recommend_sequence(beat_times, tempo, moves, phrases=max_phrases)

            # figure out which move is "active" at current_time
            active_move_idx = None
            if current_time is not None and plan:
                for i, step in enumerate(plan):
                    if step["start_time"] <= current_time <= step["end_time"]:
                        active_move_idx = i
                        break

            if plan:
                st.subheader("Suggested Moves")
                MIN_DURATION = 0.35  # seconds

                for i, step in enumerate(plan):
                    if step["duration"] is None or step["duration"] < MIN_DURATION:
                        continue

                    move_meta = moves_by_id.get(step["move_id"], {})
                    base_text = (
                        f"{i+1}. {step['name']} — beats {step['start_beat_index']+1}-{step['end_beat_index']} "
                        f"({step['start_time']:.2f}s → {step['end_time']:.2f}s, {step['duration']:.2f}s)"
                    )

                    # highlight active move
                    if active_move_idx is not None and i == active_move_idx:
                        st.markdown(
                            f"<div style='background-color:#D1E7DD;padding:4px 8px;border-radius:4px;'>"
                            f"▶ {base_text}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write(base_text)

                    # optional: show reference image if you added "image" to motion_library.json
                    img_path = move_meta.get("image")
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, width=160)
