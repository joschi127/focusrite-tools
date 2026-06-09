# Project Guidelines

## Development Principles
- **Stability & Reliability:** The automation must be robust, with clear error logging (`error.log`) and user notifications via Windows MessageBoxes for critical failures.
- **Minimal Resource Impact:** Scripts should be lightweight, using direct TCP communication and efficient port scanning with short timeouts.
- **Hardware Safety:** Ensure that hardware NVRAM flashing (`flash_hardware`) is only performed when explicitly
  requested (e.g., during standalone mode switching) to preserve hardware longevity.
- **Clean Deployment:** Use automated installation via `install.py` to handle EXE compilation (PyInstaller) and Windows
  Task Scheduler registration systematically.

## Documentation & Changelog
- **Context Awareness:** When working on tasks, always consider information from `ROADMAP.md` and `CHANGELOG.md` to
  ensure consistency with planning and past changes.
- **Changelog Requirement:** Every significant change or new feature must be documented in `CHANGELOG.md` under the `[Unreleased]` section.
- **Code Style:** Maintain uniform formatting and clear naming conventions for variables and functions, following the
  existing patterns in `focusrite_switcher.py`.
- **Markdown Formatting:** All `.md` files must maintain a maximum line length of 120 characters.

## Technical Specifications
- **Language & Runtime:** Python 3.x, recommended to run within a virtual environment (`venv`). 
    - On Debian-based systems, it is recommended to install `python3-venv` globally to simplify setup: `sudo apt install python3-venv`.
- **Build:** Compiled to a windowless executable using PyInstaller (`--onefile --noconsole`).
- **Target OS:** Windows (utilizes `win32gui`, `win32con`, and Windows Task Scheduler).
- **Network Communication:**
    - Host: `127.0.0.1` (local Focusrite Control Server).
    - Port Range: `49152` to `50000` (dynamic port detection).
    - Protocol: TCP with custom length-prefixed XML framing (`Length=XXXXXX <xml_command/>\n`).
- **Dependencies:** `pywin32`, `PyInstaller` (for build), and standard library modules (`socket`, `sys`, `os`, `time`).
- **Deployment Path:** Default installation to `%ProgramFiles%\Focusrite Switcher`.
