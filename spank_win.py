"""
spank_win.py — Windows port of taigrr/spank
Plays a random audio file from a directory when the laptop is physically 
slapped (accelerometer) or when the keyboard is smashed (fallback mode).

Usage:
    python spank_win.py --audio-dir ./sounds
    python spank_win.py --mode keyboard --audio-dir C:/my_sounds
    python spank_win.py --mode sensor --sensitivity 2.0 --cooldown 0.2

Dependencies:
    pip install pygame keyboard winsdk
"""

import argparse
import math
import sys
import time
import threading
import os
import random
from collections import deque
import pygame

# ─────────────────────────────────────────────
#  Argument Parsing
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="spank_win — slap your laptop, hear a sound."
    )
    parser.add_argument(
        "--theme",
        choices=["decent", "spicy"],
        default="decent",
        help="Which sound pack to use: 'decent' or 'spicy' (default: decent)"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "sensor", "keyboard"],
        default="auto",
        help="Detection mode: auto (default), sensor, or keyboard"
    )
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=0.12,
        help="[Sensor Mode] G-force threshold above 1G that triggers a spank (default: 0.12)"
    )
    parser.add_argument(
        "--keys",
        type=int,
        default=3,
        help="[Keyboard Mode] Number of distinct keys within the time window to trigger (default: 3)"
    )
    parser.add_argument(
        "--window",
        type=float,
        default=0.5,
        help="[Keyboard Mode] Time window in seconds for key-smash detection (default: 0.5)"
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=0.09,
        help="Seconds to ignore events after a trigger. Lower this if you want rapid-fire interruptions! (default: 0.09)"
    )
    return parser.parse_args()


# ─────────────────────────────────────────────
#  Audio Engine
# ─────────────────────────────────────────────

def init_audio(audio_dir: str) -> list:
    """Initialise pygame mixer and return a list of all sounds from the directory."""
    try:
        pygame.mixer.init()
        
        if not os.path.isdir(audio_dir):
            print(f"[Audio] ERROR: Directory '{audio_dir}' not found.")
            print(f"        Please create a folder named '{audio_dir}' and put some .mp3 or .wav files in it.")
            sys.exit(1)
            
        audio_files = []
        for f in os.listdir(audio_dir):
            if f.lower().endswith(('.mp3', '.wav')):
                audio_files.append(os.path.join(audio_dir, f))
                
        if not audio_files:
            print(f"[Audio] ERROR: No .mp3 or .wav files found in '{audio_dir}'.")
            sys.exit(1)
            
        print(f"[Audio] Loaded {len(audio_files)} sound(s) from '{audio_dir}'.")
        return audio_files
        
    except Exception as e:
        print(f"[Audio] ERROR: Could not init audio — {e}")
        print("        Make sure pygame is installed:  pip install pygame")
        sys.exit(1)


def play_audio(audio_files: list):
    """Play a random audio file asynchronously. Automatically stops the current sound."""
    try:
        if not audio_files:
            return
            
        chosen_file = random.choice(audio_files)
        
        # Explicitly stop the current track before loading a new one to prevent driver crashes
        pygame.mixer.music.stop()
        pygame.mixer.music.load(chosen_file)
        pygame.mixer.music.play()
        
    except Exception as e:
        print(f"[Audio] Playback error: {e}")


# ─────────────────────────────────────────────
#  Shared Cooldown Guard
# ─────────────────────────────────────────────

class CooldownGuard:
    def __init__(self, cooldown_seconds: float):
        self._cooldown = cooldown_seconds
        self._last_trigger = 0.0
        self._lock = threading.Lock()

    def trigger(self) -> bool:
        now = time.monotonic()
        with self._lock:
            if now - self._last_trigger >= self._cooldown:
                self._last_trigger = now
                return True
        return False


# ─────────────────────────────────────────────
#  Sensor Mode
# ─────────────────────────────────────────────

def run_sensor_mode(args, guard: CooldownGuard, audio_files: list):
    try:
        import winsdk.windows.devices.sensors as sensors
    except ImportError:
        print("[Sensor] ERROR: 'winsdk' is not installed.")
        print("         Install it with:  pip install winsdk")
        sys.exit(1)

    accel = sensors.Accelerometer.get_default()
    if accel is None:
        return False  

    print("[Sensor] Accelerometer detected. Starting in Sensor Mode.")
    print(f"[Sensor] Sensitivity threshold : {args.sensitivity} G  (above 1G baseline)")
    print(f"[Sensor] Cooldown              : {args.cooldown}s")
    print("[Sensor] Listening… press Ctrl+C to exit.\n")

    def on_reading_changed(sender, event_args):
        reading = event_args.reading
        x = reading.acceleration_x  
        y = reading.acceleration_y
        z = reading.acceleration_z

        magnitude = math.sqrt(x**2 + y**2 + z**2)
        net_force = abs(magnitude - 1.0)

        if net_force >= args.sensitivity:
            if guard.trigger():
                print(f"[Sensor] SLAP detected! Net force = {net_force:.3f}G — SPANK!")
                play_audio(audio_files)

    token = accel.add_reading_changed(on_reading_changed)
    accel.report_interval = max(accel.minimum_report_interval, 16)

    stop_event = threading.Event()
    try:
        while not stop_event.is_set():
             stop_event.wait(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        accel.remove_reading_changed(token)
        print("\n[Sensor] Listener removed.")

    return True  


# ─────────────────────────────────────────────
#  Keyboard Mode
# ─────────────────────────────────────────────

def run_keyboard_mode(args, guard: CooldownGuard, audio_files: list):
    try:
        import keyboard
    except ImportError:
        print("[Keyboard] ERROR: 'keyboard' is not installed.")
        print("           Install it with:  pip install keyboard")
        sys.exit(1)

    print("[Keyboard] Starting in Keyboard Mode.")
    print(f"[Keyboard] Trigger: {args.keys} distinct keys within {args.window * 1000:.0f}ms")
    print(f"[Keyboard] Cooldown: {args.cooldown}s")
    print("[Keyboard] Listening… press Ctrl+C to exit.\n")

    timestamps = deque()
    held_keys: set = set()
    buffer_lock = threading.Lock()

    def on_key_event(event):
        if event.event_type != keyboard.KEY_DOWN:
            if event.event_type == keyboard.KEY_UP:
                held_keys.discard(event.scan_code)
            return

        if event.scan_code in held_keys:
            return
        held_keys.add(event.scan_code)

        now = time.monotonic()

        with buffer_lock:
            cutoff = now - args.window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            timestamps.append(now)
            count = len(timestamps)

        if count >= args.keys:
            if guard.trigger():
                print(f"[Keyboard] SMASH detected! {count} keys in {args.window*1000:.0f}ms — SPANK!")
                with buffer_lock:
                    timestamps.clear()
                play_audio(audio_files)

    keyboard.hook(on_key_event)

    try:
        keyboard.wait()  
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()
        print("\n[Keyboard] Hooks removed.")


# ─────────────────────────────────────────────
#  Main Entry Point
# ─────────────────────────────────────────────

def main():
    args = parse_args()
    
    # Build the folder path based on the chosen theme (e.g., "sounds/decent")
    target_dir = os.path.join("sounds", args.theme)
    
    # Initialize audio and get the list of files from that specific folder
    audio_files = init_audio(target_dir)
    guard = CooldownGuard(args.cooldown)

    mode = args.mode
    if mode == "auto":
        sensor_available = False
        try:
            import winsdk.windows.devices.sensors as sensors
            sensor_available = sensors.Accelerometer.get_default() is not None
        except Exception:
            sensor_available = False

        if sensor_available:
            mode = "sensor"
        else:
            print("[Auto] No accelerometer detected (or winsdk unavailable).")
            print("[Auto] Falling back to Keyboard Mode.")
            mode = "keyboard"

    try:
        if mode == "sensor":
            # Pass audio_files to the sensor mode
            success = run_sensor_mode(args, guard, audio_files)
            if not success:
                print("[Sensor] Accelerometer unavailable at runtime.")
                print("[Sensor] Falling back to Keyboard Mode.")
                run_keyboard_mode(args, guard, audio_files)
        else:
            # Pass audio_files to the keyboard mode
            run_keyboard_mode(args, guard, audio_files)

    except KeyboardInterrupt:
        print("\n[Main] Interrupted by user.")

    finally:
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        print("[Main] Audio engine shut down. Exiting.")


if __name__ == "__main__":
    main()