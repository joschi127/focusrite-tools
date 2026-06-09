# Project Guidelines

## Development Principles
- **Stability & Reliability:** The automation must be robust, with clear error logging (`error.log`) and user
  notifications via Windows MessageBoxes for critical failures.
- **Minimal Resource Impact:** Scripts should be lightweight, using direct TCP communication and efficient port scanning
  with short timeouts.
- **Hardware Safety:** Ensure that hardware NVRAM flashing (`flash_hardware`) is only performed when explicitly
  requested (e.g., during standalone mode switching) to preserve hardware longevity.
- **Clean Deployment:** Use automated installation via `install.py` to handle EXE compilation (PyInstaller) and Windows
  Task Scheduler registration systematically.

## Documentation & Changelog
- **Context Awareness:** When working on tasks, always consider information from `ROADMAP.md` and `CHANGELOG.md` to
  ensure consistency with planning and past changes.
- **Changelog Requirement:** Every significant change or new feature must be documented in `CHANGELOG.md` under the
  `[Unreleased]` section.
- **Code Style:** Maintain uniform formatting and clear naming conventions for variables and functions, following the
  existing patterns in `focusrite_switcher.py`.
- **Indentation:** Use 4 spaces for indentation in **all** file types (`.md`, `.yml`/`.yaml`, `.xml`, `.py`). Do not
  use tabs or 3-space (or 2-space) indentation. This is enforced via the root `.editorconfig`, so make sure your
  editor has EditorConfig support enabled.
- **Markdown Formatting:** All `.md` files must maintain a maximum line length of 120 characters. Indents for bullet
  points should be only 2 for compatibility with GitHub rendering. (even though for other content we use 4)


## Technical Specifications
- **Language & Runtime:** Python 3.x, recommended to run within a virtual environment (`venv`). 
    - On Debian-based systems, it is recommended to install `python3-venv` globally to simplify setup:
      `sudo apt install python3-venv`.
- **Build:** Compiled to a windowless executable using PyInstaller (`--onefile --noconsole`).
- **Target OS:** Windows (utilizes `win32gui`, `win32con`, and Windows Task Scheduler).
- **Network Communication:**
    - Host: `127.0.0.1` (local Focusrite Control Server).
    - Port Range: `49152` to `50000` (dynamic port detection).
    - Protocol: TCP with custom length-prefixed XML framing (`Length=XXXXXX <xml_command/>\n`).
- **References:**
    - [Focusrite Control API Documentation](docs/focusrite_control_api/focusrite_control_api.md) (Local - **Must be consulted for all implementation changes related to server communication**)
    - [Focusrite-Midi-Control](https://github.com/raduvarga/Focusrite-Midi-Control)
    - [Focusrite-Midi-Control - device-arrival.xml](https://github.com/raduvarga/Focusrite-Midi-Control/blob/master/example%20xml/device-arrival.xml)
    - [Focusrite-Midi-Control - device-set.xml](https://github.com/raduvarga/Focusrite-Midi-Control/blob/master/example%20xml/device-set.xml)
    - [companion-module-focusrite-clarett - focusrite-client.js](https://github.com/bitfocus/companion-module-focusrite-clarett/blob/main/focusrite-client.js)
- **Dependencies:** `pywin32`, `PyInstaller` (for build), and standard library modules (`socket`, `sys`, `os`, `time`).
- **Deployment Path:** Default installation to `%ProgramFiles%\Focusrite Switcher`.
