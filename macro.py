import time, queue, random, os, sys, json, datetime
import numpy as np
import pyaudiowpatch as pyaudio
import pyautogui
from scipy.io import wavfile
from scipy.signal import resample as sp_resample

VERSION     = "v0.1"
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
WAV_PATH    = os.path.join(SCRIPT_DIR, "bite.wav")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
BLOCK       = 2048

ESC        = "\033["
RESET      = f"{ESC}0m"
BOLD       = f"{ESC}1m"
DIM        = f"{ESC}2m"
CYAN       = f"{ESC}38;2;56;189;248m"
BLUE       = f"{ESC}38;2;99;102;241m"
GREEN      = f"{ESC}38;2;52;211;153m"
YELLOW     = f"{ESC}38;2;251;191;36m"
ORANGE     = f"{ESC}38;2;251;146;60m"
RED        = f"{ESC}38;2;248;113;113m"
WHITE      = f"{ESC}38;2;243;244;246m"
GRAY       = f"{ESC}38;2;156;163;175m"
MUTED      = f"{ESC}38;2;75;85;99m"
CLEAR_LINE = f"{ESC}K"
CLEAR_DOWN = f"{ESC}J"

os.system("")
os.system(f"title Fischly {VERSION}")

EXCLUDE = ("vb-audio", "vb audio", "cable", "voicemod")
DOTS    = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

SEP      = f"{MUTED}{'─' * 50}{RESET}"
SEP_THIN = f"{MUTED}{'·' * 50}{RESET}"

DEFAULT_CONFIG = {
    "threshold":       0.75,
    "cooldown":        3.0,
    "recast_delay":    0.2,
    "failsafe_recast": 30,
    "failsafe_stop":   60,
    "device_index":    -1,
    "device_name":     "auto",
}


def is_excluded(name):
    return any(kw in name.lower() for kw in EXCLUDE)


def cursor_hide():
    sys.stdout.write(f"{ESC}?25l")
    sys.stdout.flush()


def cursor_show():
    sys.stdout.write(f"{ESC}?25h")
    sys.stdout.flush()


def clear():
    sys.stdout.write(f"{ESC}2J{ESC}H")
    sys.stdout.flush()


def ask(prompt, default=None, cast=str, validate=None):
    hint = f" {MUTED}[{RESET}{BOLD}{default}{RESET}{MUTED}]{RESET}" if default is not None else ""
    while True:
        sys.stdout.write(f"  {CYAN}›{RESET} {prompt}{hint}  ")
        sys.stdout.flush()
        raw = input().strip()
        if raw == "" and default is not None:
            return default
        try:
            val = cast(raw)
            if validate and not validate(val):
                raise ValueError
            return val
        except (ValueError, TypeError):
            print(f"  {RED}Invalid value, try again.{RESET}")


def ask_bool(prompt, default=True):
    hint = f"{BOLD}Y{RESET}{MUTED}/n{RESET}" if default else f"{MUTED}y/{RESET}{BOLD}N{RESET}"
    while True:
        sys.stdout.write(f"  {CYAN}›{RESET} {prompt}  {MUTED}[{RESET}{hint}{MUTED}]{RESET}  ")
        sys.stdout.flush()
        raw = input().strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes", "1"):
            return True
        if raw in ("n", "no", "0"):
            return False
        print(f"  {RED}Answer with y or n.{RESET}")


def list_loopback_devices(pa):
    devs = []
    for i in range(pa.get_device_count()):
        try:
            info = pa.get_device_info_by_index(i)
        except Exception:
            continue
        if not info.get("isLoopbackDevice", False):
            continue
        if is_excluded(info["name"]):
            continue
        devs.append(info)
    return devs


def run_setup(pa):
    os.system("cls")
    cursor_show()
    print(f"\n  {BOLD}{WHITE}Fischly {VERSION}{RESET}  {MUTED}· First-time setup{RESET}")
    print(f"  {SEP}\n")
    print(f"  {BOLD}Would you like to use the default config or set it up manually?{RESET}")
    print(f"  {MUTED}Default  →  recommended settings, ready in one keypress{RESET}")
    print(f"  {MUTED}Custom   →  configure each option yourself{RESET}\n")

    use_default = ask_bool("Use default config?", default=True)

    if use_default:
        cfg = dict(DEFAULT_CONFIG)
        _save_config(cfg)
        print(f"\n  {GREEN}✓ Default config saved.{RESET}")
        print(f"  {MUTED}Delete config.json at any time to reconfigure.{RESET}\n")
        return cfg

    print(f"\n  {MUTED}Press Enter to accept the value shown in brackets.{RESET}\n")
    cfg = dict(DEFAULT_CONFIG)

    print(f"  {BOLD}{WHITE}1 · Audio device{RESET}")
    loopbacks = list_loopback_devices(pa)

    if not loopbacks:
        print(f"  {YELLOW}No loopback device detected – auto mode will be used.{RESET}\n")
        cfg["device_index"] = -1
        cfg["device_name"]  = "auto"
    else:
        print(f"  {GRAY}Available loopback devices:{RESET}")
        for dev in loopbacks:
            print(f"    {MUTED}[{dev['index']:2d}]{RESET}  {dev['name']}  {MUTED}@ {int(dev['defaultSampleRate'])} Hz{RESET}")
        print()

        auto_dev = None
        try:
            auto_dev = pa.get_default_wasapi_loopback()
        except Exception:
            pass
        default_idx = (
            auto_dev["index"]
            if auto_dev and not is_excluded(auto_dev["name"])
            else loopbacks[0]["index"]
        )

        chosen = ask(
            "Device index  (-1 = auto)",
            default=default_idx,
            cast=int,
            validate=lambda v: v == -1 or any(d["index"] == v for d in loopbacks),
        )
        if chosen == -1:
            cfg["device_index"] = -1
            cfg["device_name"]  = "auto"
        else:
            match = next(d for d in loopbacks if d["index"] == chosen)
            cfg["device_index"] = chosen
            cfg["device_name"]  = match["name"]
        print()

    print(f"  {BOLD}{WHITE}2 · Detection threshold{RESET}")
    print(f"  {MUTED}How closely the sound must match to count as a bite.{RESET}")
    print(f"  {MUTED}0.0 = trigger on anything  ·  1.0 = exact match  ·  recommended: 0.75{RESET}")
    cfg["threshold"] = ask("Threshold", default=0.75, cast=float, validate=lambda v: 0.0 < v <= 1.0)
    print()

    print(f"  {BOLD}{WHITE}3 · Cooldown{RESET}")
    print(f"  {MUTED}Minimum gap between two catches (prevents double-triggers).{RESET}")
    cfg["cooldown"] = ask("Cooldown (s)", default=3.0, cast=float, validate=lambda v: v >= 0.5)
    print()

    print(f"  {BOLD}{WHITE}4 · Recast delay{RESET}")
    print(f"  {MUTED}Wait time between the catch click and the recast click.{RESET}")
    cfg["recast_delay"] = ask("Recast delay (s)", default=0.2, cast=float, validate=lambda v: v >= 0.0)
    print()

    print(f"  {BOLD}{WHITE}5 · Auto-recast failsafe{RESET}")
    print(f"  {MUTED}If no bite is detected for X seconds, right-click to recast automatically.{RESET}")
    if ask_bool("Enable?", default=True):
        cfg["failsafe_recast"] = ask("Delay (s)", default=30, cast=int, validate=lambda v: v >= 5)
    else:
        cfg["failsafe_recast"] = 0
    print()

    print(f"  {BOLD}{WHITE}6 · Full-stop failsafe{RESET}")
    print(f"  {MUTED}If no bite is detected for X seconds, stop the macro entirely.{RESET}")
    print(f"  {MUTED}Useful to avoid detection if something goes wrong.{RESET}")
    if ask_bool("Enable?", default=True):
        fs_stop_default = max(cfg["failsafe_recast"] + 30, 60) if cfg["failsafe_recast"] else 60
        cfg["failsafe_stop"] = ask("Delay (s)", default=fs_stop_default, cast=int, validate=lambda v: v >= 10)
    else:
        cfg["failsafe_stop"] = 0
    print()

    fs_r_str = f"{cfg['failsafe_recast']}s" if cfg["failsafe_recast"] else f"{MUTED}off{RESET}"
    fs_s_str = f"{cfg['failsafe_stop']}s"   if cfg["failsafe_stop"]   else f"{MUTED}off{RESET}"

    print(f"  {SEP}")
    print(f"  {BOLD}{WHITE}Summary{RESET}\n")
    print(f"  {GRAY}Device           {MUTED}·{RESET}  {cfg['device_name']}{MUTED} (index {cfg['device_index']}){RESET}")
    print(f"  {GRAY}Threshold        {MUTED}·{RESET}  {cfg['threshold']:.0%}")
    print(f"  {GRAY}Cooldown         {MUTED}·{RESET}  {cfg['cooldown']}s")
    print(f"  {GRAY}Recast delay     {MUTED}·{RESET}  {cfg['recast_delay']}s")
    print(f"  {GRAY}Failsafe recast  {MUTED}·{RESET}  {fs_r_str}")
    print(f"  {GRAY}Failsafe stop    {MUTED}·{RESET}  {fs_s_str}")
    print(f"  {SEP}\n")

    _save_config(cfg)
    print(f"  {GREEN}✓ Config saved to config.json{RESET}\n")

    if ask_bool("Launch Fischly now?", default=True):
        return cfg

    print(f"\n  {MUTED}Run start.bat when you're ready.{RESET}\n")
    return None


def _save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_config(pa):
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception as e:
            print(f"  {YELLOW}config.json is corrupted ({e}) — re-running setup.{RESET}\n")
    return run_setup(pa)


def find_loopback(pa, forced_index=-1):
    if forced_index >= 0:
        try:
            info = pa.get_device_info_by_index(forced_index)
            return info, int(info["defaultSampleRate"])
        except Exception as e:
            print(f"  {RED}Forced device [{forced_index}] not found: {e}{RESET}")
            return None, 44100

    try:
        info = pa.get_default_wasapi_loopback()
        if info and not is_excluded(info["name"]):
            return info, int(info["defaultSampleRate"])
    except Exception:
        pass

    for i in range(pa.get_device_count()):
        try:
            info = pa.get_device_info_by_index(i)
        except Exception:
            continue
        if not info.get("isLoopbackDevice", False):
            continue
        if is_excluded(info["name"]):
            continue
        return info, int(info["defaultSampleRate"])

    return None, 44100


def dominant_freqs(data):
    fft = np.abs(np.fft.rfft(data, n=BLOCK))
    fft /= fft.max() + 1e-9
    return fft


def load_ref(path, target_sr):
    rate, data = wavfile.read(path)
    if data.ndim > 1:
        data = data[:, 0]
    if rate != target_sr:
        data = sp_resample(data, int(len(data) * target_sr / rate))
    data = data.astype(np.float32)
    mx = np.max(np.abs(data))
    data = data / mx if mx > 1e-9 else data
    best_energy, best_chunk = 0, data[:BLOCK]
    for i in range(0, len(data) - BLOCK, BLOCK // 2):
        chunk = data[i:i + BLOCK]
        energy = np.sum(chunk ** 2)
        if energy > best_energy:
            best_energy, best_chunk = energy, chunk
    return dominant_freqs(best_chunk)


def sim(a, b):
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / d) if d > 1e-9 else 0.0


def make_bar(val, threshold, width=32):
    val   = max(0.0, min(1.0, val))
    fill  = int(round(val * width))
    t_pos = int(round(threshold * width))
    chars = []
    for i in range(width):
        if i < fill:
            if i >= t_pos:
                chars.append(f"{BOLD}{GREEN}█{RESET}")
            elif i >= int(t_pos * 0.78):
                chars.append(f"{YELLOW}█{RESET}")
            else:
                chars.append(f"{CYAN}█{RESET}")
        else:
            if i == t_pos:
                chars.append(f"{BOLD}{RED}│{RESET}")
            else:
                chars.append(f"{MUTED}░{RESET}")
    return "".join(chars)


def make_countdown_bar(elapsed, total, width=22):
    if total <= 0:
        return f"{MUTED}{'░' * width}{RESET}"
    ratio = min(elapsed / total, 1.0)
    fill  = int(round(ratio * width))
    if ratio < 0.5:
        col = GREEN
    elif ratio < 0.8:
        col = YELLOW
    else:
        col = RED
    return f"{col}{'█' * fill}{RESET}{MUTED}{'░' * (width - fill)}{RESET}"


def fmt_ts(ts):
    if ts is None:
        return f"{MUTED}—{RESET}"
    return f"{GRAY}{datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')}{RESET}"


def render(start_time, count, score, peak_score, last_det, last_catch_ts,
           status, status_icon, device_name, cfg, dot_idx):
    now     = time.time()
    elapsed = max(1, int(now - start_time))
    h, rem  = divmod(elapsed, 3600)
    m, s    = divmod(rem, 60)
    uptime  = f"{h:02d}:{m:02d}:{s:02d}"
    rate    = (count / elapsed) * 3600

    idle      = now - last_det
    idle_s    = int(idle)
    fs_stop   = cfg["failsafe_stop"]
    fs_recast = cfg["failsafe_recast"]
    threshold = cfg["threshold"]

    if fs_recast:
        cd_bar = make_countdown_bar(idle, fs_recast, width=24)
        if idle_s >= fs_recast:
            cd_right = f"{BOLD}{YELLOW}  recasting{RESET}"
        elif fs_stop and idle_s >= fs_stop - 10:
            cd_right = f"{BOLD}{RED}  stopping soon!{RESET}"
        else:
            pct = min(idle_s / fs_recast, 1.0)
            cd_right = f"  {MUTED}{idle_s}s{RESET}"
        idle_row = f"{cd_bar}{cd_right}"
    else:
        idle_row = f"{MUTED}{idle_s}s idle  ·  no failsafe{RESET}"

    sig_bar = make_bar(score, threshold)
    col     = GREEN if score >= threshold else (YELLOW if score >= threshold * 0.78 else CYAN)
    spinner = f"{CYAN}{DOTS[dot_idx % len(DOTS)]}{RESET}"

    catch_col = GREEN if count > 0 else MUTED

    LINE = f"  {MUTED}{ESC}0m{MUTED}{'─' * 80}{RESET}"

    return (
        f"{ESC}H"

        f"\n  {BOLD}{CYAN}Fischly{RESET} {MUTED}{VERSION}{RESET}   {MUTED}│{RESET}   {status_icon}  {status}{CLEAR_LINE}\n"

        f"\n"

        f"{LINE}{CLEAR_LINE}\n"
        f"  {BOLD}{catch_col}{count:>4}{RESET}{GRAY}  fish{RESET}   "
        f"{MUTED}│{RESET}   {MUTED}uptime {RESET}{GRAY}{uptime}{RESET}   "
        f"{MUTED}│{RESET}   {BOLD}{WHITE}{rate:.1f}{RESET}{MUTED}/h{RESET}   "
        f"{MUTED}│{RESET}   {MUTED}last {RESET}{fmt_ts(last_catch_ts)}{CLEAR_LINE}\n"
        f"{LINE}{CLEAR_LINE}\n"

        f"\n"

        f"  {MUTED}signal{RESET}   {sig_bar}   {BOLD}{col}{score:5.1%}{RESET}   {MUTED}gate {RESET}{WHITE}{threshold:.0%}{RESET}{CLEAR_LINE}\n"

        f"\n"

        f"{LINE}{CLEAR_LINE}\n"
        f"  {MUTED}idle  {RESET}   {idle_row}{CLEAR_LINE}\n"
        f"{LINE}{CLEAR_LINE}\n"

        f"\n"

        f"  {MUTED}Ctrl+C to quit   ·   Made by NotLoann{RESET}{CLEAR_LINE}\n"
        f"{CLEAR_DOWN}"
    )


def print_startup_info(device_name, actual_sr, cfg):
    clear()
    LINE = f"  {MUTED}{'─' * 80}{RESET}"
    print(f"\n  {BOLD}{CYAN}Fischly{RESET} {MUTED}{VERSION}{RESET}   {GREEN}ready{RESET}\n")
    print(LINE)
    print(f"  {MUTED}listening on{RESET}  {WHITE}{device_name}{RESET}  {MUTED}@ {actual_sr} Hz{RESET}")
    print(f"{LINE}\n")
    time.sleep(0.6)


def main():
    cursor_hide()
    clear()

    pa = pyaudio.PyAudio()

    try:
        cfg = load_config(pa)
        if cfg is None:
            return

        THRESHOLD    = cfg["threshold"]
        COOLDOWN     = cfg["cooldown"]
        RECAST_DELAY = cfg["recast_delay"]
        FS_RECAST    = cfg["failsafe_recast"]
        FS_STOP      = cfg["failsafe_stop"]

        clear()
        cursor_hide()

        dev_info, actual_sr = find_loopback(pa, forced_index=cfg["device_index"])

        if dev_info is None:
            cursor_show()
            print(f"\n  {RED}✗ No loopback device found.{RESET}")
            print(f"  {YELLOW}Make sure your audio output is active, then relaunch.")
            print(f"  Delete config.json to re-run setup.{RESET}\n")
            return

        device_name  = dev_info["name"]
        device_index = dev_info["index"]
        channels     = dev_info["maxInputChannels"]
        actual_sr    = int(dev_info["defaultSampleRate"])

        try:
            ref_fft = load_ref(WAV_PATH, actual_sr)
        except Exception as e:
            cursor_show()
            print(f"\n  {RED}✗ Could not load bite.wav: {e}{RESET}")
            print(f"  {YELLOW}Make sure bite.wav is in the same folder as macro.py.{RESET}\n")
            return

        audio_q = queue.Queue(maxsize=64)
        stream_error = [None]

        def pa_callback(in_data, frame_count, time_info, status_flags):
            try:
                arr = np.frombuffer(in_data, dtype=np.float32).copy()
                if channels > 1:
                    arr = arr[::channels]
                if not audio_q.full():
                    audio_q.put_nowait(arr[:BLOCK])
            except Exception as e:
                stream_error[0] = e
            return (None, pyaudio.paContinue)

        try:
            stream = pa.open(
                format=pyaudio.paFloat32,
                channels=channels,
                rate=actual_sr,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=BLOCK,
                stream_callback=pa_callback,
            )
        except Exception as e:
            cursor_show()
            print(f"\n  {RED}✗ Could not open audio stream: {e}{RESET}")
            print(f"  {YELLOW}Try selecting a different device in config.json, or delete it to re-run setup.{RESET}\n")
            return

        clear()
        cursor_hide()

        start_time    = time.time()
        last_det      = start_time
        last_catch_ts = None
        count         = 0
        recast_done   = False
        current_score = 0.0
        peak_score    = 0.0
        dot_idx       = 0
        status        = f"{GREEN}Active{RESET}"
        status_icon   = f"{GREEN}●{RESET}"
        last_render   = 0.0
        last_dot_upd  = 0.0
        running       = True

        stream.start_stream()

        try:
            while running and stream.is_active():
                now             = time.time()
                time_since_last = now - last_det

                if stream_error[0]:
                    status      = f"Stream error: {stream_error[0]}"
                    status_icon = f"{RED}●{RESET}"
                    running     = False
                    break

                if now - last_dot_upd >= 0.12:
                    dot_idx      = (dot_idx + 1) % len(DOTS)
                    last_dot_upd = now

                if FS_RECAST and time_since_last >= FS_RECAST and not recast_done:
                    status      = f"{YELLOW}Recasting...{RESET}"
                    status_icon = f"{YELLOW}●{RESET}"
                    sys.stdout.write(render(start_time, count, current_score, peak_score,
                                           last_det, last_catch_ts, status, status_icon,
                                           device_name, cfg, dot_idx))
                    sys.stdout.flush()
                    pyautogui.click(button="right")
                    recast_done = True
                    status      = f"{GREEN}Active{RESET}"
                    status_icon = f"{GREEN}●{RESET}"

                if FS_STOP and time_since_last >= FS_STOP:
                    status      = f"{RED}Stopped by failsafe{RESET}"
                    status_icon = f"{RED}●{RESET}"
                    sys.stdout.write(render(start_time, count, current_score, peak_score,
                                           last_det, last_catch_ts, status, status_icon,
                                           device_name, cfg, dot_idx))
                    sys.stdout.flush()
                    pyautogui.press("esc")
                    running = False
                    break

                try:
                    chunk = audio_q.get(timeout=0.05)
                except queue.Empty:
                    if now - last_render >= 0.1:
                        sys.stdout.write(render(start_time, count, current_score, peak_score,
                                               last_det, last_catch_ts, status, status_icon,
                                               device_name, cfg, dot_idx))
                        sys.stdout.flush()
                        last_render = now
                    continue

                if len(chunk) < BLOCK:
                    continue

                live_fft      = dominant_freqs(chunk[:BLOCK])
                current_score = sim(live_fft, ref_fft)

                if current_score > peak_score:
                    peak_score = current_score

                if current_score >= THRESHOLD and now - last_det >= COOLDOWN:
                    last_det      = now
                    last_catch_ts = now
                    recast_done   = False
                    count        += 1
                    status        = f"{BOLD}{GREEN}Fish #{count} caught!{RESET}"
                    status_icon   = f"{GREEN}●{RESET}"
                    sys.stdout.write(render(start_time, count, current_score, peak_score,
                                           last_det, last_catch_ts, status, status_icon,
                                           device_name, cfg, dot_idx))
                    sys.stdout.flush()
                    pyautogui.click(button="right")
                    time.sleep(RECAST_DELAY + random.uniform(0.1, 0.35))
                    pyautogui.click(button="right")
                    status      = f"{GREEN}Active{RESET}"
                    status_icon = f"{GREEN}●{RESET}"

                if now - last_render >= 0.08:
                    sys.stdout.write(render(start_time, count, current_score, peak_score,
                                           last_det, last_catch_ts, status, status_icon,
                                           device_name, cfg, dot_idx))
                    sys.stdout.flush()
                    last_render = now

        except KeyboardInterrupt:
            status      = f"{MUTED}Stopped by user{RESET}"
            status_icon = f"{MUTED}●{RESET}"

        stream.stop_stream()
        stream.close()

    finally:
        pa.terminate()
        cursor_show()

    elapsed     = max(1, time.time() - start_time)
    elapsed_min = int(elapsed / 60)
    rate        = (count / elapsed) * 3600

    LINE = f"  {MUTED}{'─' * 80}{RESET}"
    clear()
    print(f"\n  {BOLD}{CYAN}Fischly{RESET} {MUTED}{VERSION}{RESET}\n")
    print(LINE)
    print(f"  {BOLD}{WHITE}Session over{RESET}")
    print(f"{LINE}\n")
    print(f"  {BOLD}{GREEN}{count}{RESET}{GRAY}  fish{RESET}   {MUTED}·{RESET}   {BOLD}{CYAN}{rate:.1f}{RESET}{MUTED}/h{RESET}   {MUTED}·{RESET}   {WHITE}{elapsed_min} min{RESET}")
    pk_col_end = GREEN if peak_score >= cfg["threshold"] else YELLOW
    print(f"{LINE}\n")
    if FS_STOP and status == f"{RED}Stopped by failsafe{RESET}":
        print(f"  {YELLOW}No fish detected for {FS_STOP}s — macro stopped automatically.")
        print(f"  Relaunch the macro to start fishing again!{RESET}\n")
    print(f"  {MUTED}Thank you for using Fischly! See you soon!{RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        cursor_show()
        print(f"\n  {RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
    os.system("pause > nul")
