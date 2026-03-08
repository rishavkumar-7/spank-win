# 💥 Spank (Windows Edition)

**Slap your Windows laptop, it yells back.**

This entire project was **vibe coded** and heavily inspired by the brilliant original macOS tool [taigrr/spank](https://github.com/taigrr/spank). I wanted this exact same hilarious functionality, but built natively for Windows laptops!

## ✨ How it Works
Unlike Macs, Windows hardware is wild and varied. This script features an **Auto-Detect & Fallback System**:
1. **Sensor Mode (The Real Deal):** If you have a 2-in-1 laptop or tablet (like a Surface or Lenovo Yoga), it taps directly into the native Windows `HID Sensor Collection V2` accelerometer using `winsdk`. When it detects a physical G-force spike (a slap), it yells.
2. **Keyboard Mode (The Fallback):** If your laptop doesn't have an accelerometer, the script automatically falls back to Keyboard Mode. Instead of slapping the screen, just smash the keyboard (hit 3+ keys at the exact same time), and it triggers the audio!

## 📦 Installation

1. Clone this repository (or download the ZIP):
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME

2. Install the required Python dependencies:
   pip install -r requirements.txt
   
*(Note: This installs `pygame` for audio, `keyboard` for the fallback, and `winsdk` to read the Windows accelerometer).*

## 🚀 Usage

Run the script from your terminal. By default, it will auto-detect your hardware and use the "decent" sound pack.

python spank_win.py

### 🌶️ Themes (Sound Packs)
The repository comes with bundled sound themes. You can easily switch between them:

# Play safe/funny sounds (Default)
python spank_win.py --theme decent

# Play the spicy/escalating sounds
python spank_win.py --theme spicy

*(Want to add your own? Just drop your `.mp3` or `.wav` files into the `sounds/decent/` or `sounds/spicy/` folders!)*

### 🛠️ Advanced Controls & Tweaks

**Force Keyboard Mode:** (If you have a sensor but just want to smash keys instead)
python spank_win.py --mode keyboard

**Adjust Sensor Sensitivity:** (Default is `0.12`G. Lower it to make it trigger on lighter taps)
python spank_win.py --mode sensor --sensitivity 0.5

**Adjust the Audio Cooldown:** (Default is `0.09` seconds. Lower it if you want to be able to rapid-fire interrupt the sounds)
python spank_win.py --cooldown 0.2

## ⚠️ Troubleshooting Sensor Mode
If you are running Windows 11 on a 2-in-1 laptop and the script says "Accelerometer detected" but it doesn't react when you hit it:
* **Turn off Rotation Lock!** Windows cuts power to the accelerometer when Rotation Lock is turned ON in your Action Center to save battery. Turn it off, and the script will wake up.

## 🙏 Credits
Massive shoutout to [@taigrr](https://github.com/taigrr) for the original macOS `spank` concept. Peak engineering.