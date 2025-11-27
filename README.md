# 🎵 Dance Choreography Ideation Assistant

**Generate dance move ideas automatically from any song.**

This app helps dancers quickly brainstorm choreography by analyzing music, detecting beats/tempo, and suggesting movement ideas from a custom curated motion library. Built with **Python**, **Librosa**, and **Streamlit**, the tool enables fast choreo prototyping.

---

🌐 Live Demo

You can try the app instantly:

👉 https://dance-choreo-assistant-f25-17209.streamlit.app/

Upload any audio file, preview tempo + beat structure, and browse automatically generated movement ideas with visual references.

---

## ✨ Features

### 🔊 **Audio Analysis**

* Upload an `.mp3`, `.wav`, or `.m4a`
* Detects:

  * Global tempo (BPM)
  * Beat timestamps
  * Section tempos (per 8-count)
  * Song structure based on rhythmic changes

### 🕺 **Choreography Suggestions**

The system generates dance move ideas aligned to:

* Beat timing
* Tempo ranges
* Move length (1–4 beats)
* Style, energy, and difficulty metadata

Uses a large JSON-based motion library with:

* Hip-hop basics
* K-pop vocabulary
* House steps
* Popping/waving
* Contemporary textures
* Gestures, footwork, grooves, level changes

### 🎛 **Customizable Output**

* Choose how many phrases (8-counts) to generate
* Limit number of sections shown
* Scroll through move-by-move breakdown with:

  * Beat indices
  * Start/end timestamps
  * Move durations

---

## 🧠 How It Works (Technical Overview)

### 🎧 1. Audio Processing

Using **Librosa**, the app:

* Computes onset strength
* Detects beat positions
* Calculates tempo with `librosa.beat.beat_track`
* Approximates 8-count groupings with beat index chunking

### 🧩 2. Move Matching Logic

Each move in `motion_library.json` includes:

* Beats required
* Tempo constraints
* Style tags
* Difficulty
* Notes / functional tags

`recommend_sequence()`:

* Iterates through beats
* Chooses a move that fits:

  * Beat length
  * Tempo range
  * Not repeated too frequently
* Advances the beat pointer
* Builds a timeline of move recommendations

### 🎨 3. Visuals (GIF/Video)

Each move can optionally include:

```json
"image": "images/running_man.gif"
```

Streamlit displays it automatically.

---

## 🖼 Adding New Move Visuals

Place any `.gif`, `.png`, or `.mp4` into the `images/` folder and update your JSON:

```json
{
  "id": "running_man",
  "name": "Running Man",
  "beats": 2,
  "image": "images/running_man.gif"
}
```
