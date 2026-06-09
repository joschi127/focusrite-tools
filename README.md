# Focusrite Scarlett 18i8 Gen 2 - Routing Automation

This project automates the routing profile switching on the Focusrite Scarlett 18i8 (2nd Gen) audio interface to seamlessly handle transitions between active PC usage and standalone operations.

- **Windows Playback Mode:** Mutes all hardware inputs (`playback_only`) so that system audio and DAW playback operate smoothly without any distracting direct hardware monitoring.
- **Standalone Mode (Laptop Off/Disconnected):** The Scarlett automatically falls back to its internal non-volatile memory (NVRAM) configuration (e.g., `8 Channel Analogue`), allowing instruments, synths, and microphones to be monitored directly through your speakers or headphones without a computer.

---

## ?? Project Structure

Ensure the following files are located within the same directory:
1. `focusrite_switcher.py` - The core automation script handling TCP/XML communications with the Focusrite background server.
2. `install.py` - The automated installer script (Compiles the code to an invisible EXE and registers the Windows Task).
3. `README.md` - This instruction file.

---

## ??? One-Time Hardware Preparation (Standalone Profile)

Before deploying the automated scripts, you must flash your preferred "Laptop-Off" routing preset directly into the Scarlett's physical memory:

1. Launch the official **Focusrite Control** desktop application.
2. Configure your mixing layouts exactly how you want them to behave in standalone mode (e.g., load the built-in **"8 Channel Analogue"** preset so all line inputs route straight to your main monitor outputs).
3. Navigate to the top menu and select **File** -> **Save to Hardware**. This burns your routing preference permanently into the hardware's NVRAM.
4. Close Focusrite Control.

From this point on, your standalone configuration is safely baked into the audio interface itself.

---

## ?? Installation & Deployment

Because Windows safeguards system directories (`C:\Program Files`) and requires elevated permissions for the Task Scheduler API, you must run the installation locally via an Administrator terminal.

### 1. Move Files to a Local Directory
If you downloaded or cloned this repository onto a network share or network drive, **copy the entire folder to a local hard drive first** (e.g. into `C:\Users\username\Downloads\focusrite_switcher`). Windows security parameters prevent execution directly from UNC network locations.

### 2. Open an Elevated Command Prompt
1. Press the **Windows Key** on your keyboard.
2. Type `cmd` into the search bar.
3. Right-click on **Command Prompt** and select **"Run as Administrator"**.

### 3. Install Prerequisites & Run Installer
#### Windows
Navigate to your local folder inside the terminal window, set up a virtual environment, install the required packages, and execute the setup script (replace the path in the first command with your actual local directory path):

```cmd
cd /d "C:\Program Files\Focusrite\Focusrite Control\Server"
AddFirewallException.cmd
AddFirewallException.cmd
:: restart might be needed

cd /d "C:\Users\username\Downloads\focusrite_switcher"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python install.py
```

#### Debian/Ubuntu (Development/Testing)
On Debian-based systems, you can simplify the virtual environment setup by installing the `python3-venv` package globally:

```bash
sudo apt update
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Post-Installation Verification
Open a standard Command Prompt window and execute the following command to manually trigger your new startup task:
```cmd
schtasks /run /tn "Focusrite_Playback_Startup"
```
