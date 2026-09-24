<div align="center">

# 🎣 Fischly

**Hypixel Skyblock fishing macro — Fully made in Python**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)

</div>

---

Fischly listens to your system audio via **WASAPI loopback** and detects the Hypixel Skyblock fishing bite sound in real-time using FFT signal matching. When a bite is detected, it right-clicks to catch and recasts automatically.

No virtual audio drivers needed — works with any headset or speakers.

---

## Setup

1. **Install Python 3.10+** — check *Add Python to PATH* during install
2. **Run `start.bat`** — installs dependencies and launches the macro

On first launch you'll be asked to use the default config or set it up manually.

---

## Config

| Key | Default | Description |
|---|---|---|
| `threshold` | `0.75` | Match sensitivity (0.0–1.0) |
| `cooldown` | `3.0` | Min seconds between catches |
| `recast_delay` | `0.2` | Delay between catch and recast click |
| `failsafe_recast` | `30` | Idle seconds before auto-recast (`0` = off) |
| `failsafe_stop` | `60` | Idle seconds before full stop (`0` = off) |

Delete `config.json` and relaunch to reconfigure.

---

## Tuning

- **Bar never reaches the gate** → lower `threshold` to `0.60` or re-record `bite.wav`
- **False positives** → raise `threshold` to `0.85`
- **Double-catches** → increase `cooldown`
- **Wrong audio device** → delete `config.json`, relaunch, and pick the correct device

---
