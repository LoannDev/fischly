<div align="center">

# 🎣 Fischly

**Audio-based fishing macro — no VB-Cable, no screen capture, no pixel reading.**

Fischly listens to your system audio in real-time and detects the fish bite sound using FFT signal matching. When it hears a match, it right-clicks to catch the fish and recasts automatically.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

</div>

---

## How it works

Fischly captures your system audio output directly via **WASAPI loopback** — the native Windows API that taps into whatever is playing through your speakers or headset, without any virtual audio driver.

Each audio frame is transformed into a frequency spectrum via FFT and compared against a reference recording of the bite sound (`son.wav`). When the similarity score crosses the detection threshold, Fischly fires two right-clicks — one to catch, one to recast.

```
System audio → WASAPI loopback → FFT → cosine similarity → threshold → right-click × 2
```

---

## Requirements

- Windows 10 or 11
- Python 3.10+

All Python dependencies are installed automatically by `start.bat`:

| Package | Purpose |
|---|---|
| `pyaudiowpatch` | WASAPI loopback audio capture |
| `numpy` | FFT processing |
| `scipy` | WAV loading + resampling |
| `pyautogui` | Mouse click automation |

---

## Setup

**1. Clone or download the repo**

```
git clone https://github.com/yourname/fischly
cd fischly
```

**2. Add your bite sound**

Record or extract the fish bite sound from the game and save it as `son.wav` in the same folder as `macro.py`.

**3. Launch**

Double-click `start.bat`. It will:
- Check that Python is installed
- Install any missing packages automatically
- Launch the macro

On first launch, Fischly will ask whether you want to use the **default config** or set it up manually.

---

## Configuration

Config is stored in `config.json` and created automatically on first launch.

| Key | Default | Description |
|---|---|---|
| `threshold` | `0.75` | Signal match required to trigger a catch (0.0–1.0) |
| `cooldown` | `3.0` | Minimum seconds between two catches |
| `recast_delay` | `0.2` | Pause between the catch click and the recast click |
| `failsafe_recast` | `30` | Seconds idle before auto-recasting (`0` = off) |
| `failsafe_stop` | `60` | Seconds idle before stopping the macro entirely (`0` = off) |
| `device_index` | `-1` | Audio device index (`-1` = auto-detect) |

**To reconfigure:** delete `config.json` and relaunch.

---

## Dashboard

```
  Fischly v0.1   │   ●  Active

  ────────────────────────────────────────────────────────────────────────────────
     7  fish   │   uptime 00:12:44   │   32.8/h   │   last 15:03:21
  ────────────────────────────────────────────────────────────────────────────────

  signal   ████████████████████████│░░░░░░░░   81.3%   gate 75%  ⠸


  ────────────────────────────────────────────────────────────────────────────────
  idle     ████████████░░░░░░░░░░░░   12s
  ────────────────────────────────────────────────────────────────────────────────

  Ctrl+C to quit   ·   delete config.json to reconfigure
```

| Element | Description |
|---|---|
| **●** | Status dot — green (active), yellow (recasting), red (stopped) |
| **signal bar** | Live FFT match score — fills cyan → yellow → green past the gate |
| **gate** | The threshold line — detection fires when the bar crosses it |
| **idle bar** | Time since last catch — fills up toward the failsafe limit |

---

## Failsafes

Fischly has two built-in failsafes to prevent getting stuck or macro-detected:

- **Recast failsafe** — if no fish is detected for N seconds, right-clicks to recast automatically
- **Stop failsafe** — if no fish is detected for N seconds, presses Escape and stops the macro entirely

Both can be disabled or tuned in the config.

---

## Tuning tips

- **Signal never reaches the gate** — your `threshold` may be too high, or the bite sound in `son.wav` doesn't match what's playing. Try lowering the threshold to `0.60` and see if the bar reacts.
- **Too many false positives** — raise the threshold toward `0.85`.
- **Double-catches** — increase `cooldown`.
- **Wrong audio device selected** — delete `config.json`, relaunch, and pick the correct device index from the list shown during setup.

---

## File structure

```
fischly/
├── macro.py       # Main script
├── start.bat      # Launcher (checks deps, starts macro)
├── son.wav        # Bite sound reference (you provide this)
└── config.json    # Auto-generated on first launch
```

---

<div align="center">
<sub>Built for Windows · Requires Python 3.10+</sub>
</div>
