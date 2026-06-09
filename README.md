# Focusrite Tools

A collection of utilities for Focusrite Scarlett audio interfaces.

## Tools

### Focusrite Switcher
This tool automates the routing profile switching on the Focusrite Scarlett 18i8 (2nd Gen) audio interface to
seamlessly handle transitions between active PC usage and standalone operations.

- **Windows Playback Mode:** Mutes all hardware inputs (`playback_only`) so that system audio and DAW playback operate
  smoothly without any distracting direct hardware monitoring.
- **Standalone Mode (Laptop Off/Disconnected):** The Scarlett automatically falls back to its internal non-volatile
  memory (NVRAM) configuration (e.g., `8 Channel Analogue`), allowing instruments, synths, and microphones to be
  monitored directly through your speakers or headphones without a computer.

---

## Project Structure

- `docs/` - Project documentation.
  - `focusrite_control_api/` - Documentation of the Focusrite Control Server XML API.
- `tools/` - Contains individual Focusrite utilities.
  - `switcher/` - The Focusrite Switcher tool.
    - `focusrite_switcher.py` - Core automation script.
    - `install.py` - Automated installer script for Windows deployment.
    - `send_test/` - Tool for testing communication with Focusrite Control Server.
    - `focusrite_send_test.py` - Script to send XML commands to the server.
- `requirements.txt` - Project dependencies.
- `README.md` - This instruction file.

---

## One-Time Hardware Preparation (Standalone Profile)
(For Switcher tool)

Before deploying the automated scripts, you must flash your preferred "Laptop-Off" routing preset directly into the
Scarlett's physical memory:

1. Launch the official **Focusrite Control** desktop application.
2. Configure your mixing layouts exactly how you want them to behave in standalone mode (e.g., load the built-in
    **"8 Channel Analogue"** preset so all line inputs route straight to your main monitor outputs).
3. Close Focusrite Control. This will automatically write the current routing preference into the hardware's NVRAM.

---

## ?? Installation & Deployment

Because Windows safeguards system directories (`C:\Program Files`) and requires elevated permissions for the Task
Scheduler API, you must run the installation locally via an Administrator terminal.

### 1. Move Files to a Local Directory
If you downloaded or cloned this repository onto a network share or network drive, **copy the entire folder to a local
hard drive first** (e.g. into `C:\Users\username\Downloads\focusrite-tools`). Windows security parameters prevent
execution directly from UNC network locations.

### 2. Open an Elevated Command Prompt
1. Press the **Windows Key** on your keyboard.
2. Type `cmd` into the search bar.
3. Right-click on **Command Prompt** and select **"Run as Administrator"**.

### 3. Install Prerequisites & Run Installer
Navigate to your local folder inside the terminal window, set up a virtual environment, install the required packages,
and execute the setup script (replace the path in the first command with your actual local directory path):

        cd /d "C:\Program Files\Focusrite\Focusrite Control\Server"
        AddFirewallException.cmd
        AddFirewallException.cmd
        :: restart might be needed
        
        cd /d "C:\Users\username\Downloads\focusrite-tools\tools\switcher"
        python -m venv .venv
        .venv\Scripts\activate
        pip install -r ../../requirements.txt
        python install.py

### 4. Post-Installation Verification
Open a standard Command Prompt window and execute the following command to manually trigger your new startup task:

        schtasks /run /tn "Focusrite_Switcher_Startup"

---

## References

For further details on the Focusrite Control protocol and XML structure, the following resources are used as reference:

- [Focusrite Control API Documentation](docs/focusrite_control_api/focusrite_control_api.md) (Local)
- [Focusrite-Midi-Control](https://github.com/raduvarga/Focusrite-Midi-Control)
- [Focusrite-Midi-Control - device-arrival.xml](https://github.com/raduvarga/Focusrite-Midi-Control/blob/master/example%20xml/device-arrival.xml)
- [Focusrite-Midi-Control - device-set.xml](https://github.com/raduvarga/Focusrite-Midi-Control/blob/master/example%20xml/device-set.xml)
- [companion-module-focusrite-clarett - focusrite-client.js](https://github.com/bitfocus/companion-module-focusrite-clarett/blob/main/focusrite-client.js)

---

## ?? Development and Testing

### Debian/Ubuntu (Development/Testing)
On Debian-based systems, you can use the `venv` virtual environment setup by installing the `python3-venv` package:

        sudo apt update
        sudo apt install python3-venv
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
