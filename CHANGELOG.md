# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added response parsing to `focusrite_send_test.py` to extract and print specific item values (IDs 55, 798, 799) for
  easier verification of changes.
- Added technical references for Focusrite protocol implementation in `README.md` and `.junie/AGENTS.md`.
- Added local Focusrite Control API documentation under `docs/focusrite_control_api/`, including XML dumps and usage
  guides.
- Improved Focusrite Control Server communication by handling delayed full-state dumps that arrive only after the first
  command.
- Simplified `focusrite_send_test.py` to send both handshake and command before awaiting a unified response.
- Updated `focusrite_switcher.py` to handle large multi-packet responses by resetting the receive timeout upon data
  arrival.

### Changed
- Renamed configuration key `routing` to `profiles`
- Renamed `playback_only` to `routing_playback_only` and `standalone` to `routing_standalone` in configuration.
- Updated `focusrite_switcher.py` to match the new configuration format using `profiles` and handle any profile name
  from CLI.

### Added
- Project restructuring into `focusrite-tools`, making `focusrite-switcher` one of multiple potential tools.
- New directory structure: `tools/switcher/` contains the switcher logic and snapshot files.
- Markdown formatting rule: All `.md` files now maintain a maximum line length of 120 characters.
- Warning mechanism in `focusrite_switcher.py` to notify the user (via MessageBox on Windows or console otherwise) when
  no response or a timeout occurs during server communication.

### Changed
- Removed hardcoded configuration defaults from `focusrite_switcher.py`.
- Switched to reading default configuration from `tools/switcher/config.default.yml`.
- Added support for `~` (null) in `config.yml` to fall back to `config.default.yml` values.
- Updated `install.py` to support the new project structure and correctly locate `focusrite_switcher.py` and snapshot
  files.
- Renamed the project focus from a single tool to a suite of Focusrite-related utilities.
- Moved `install.py` to `tools/switcher/` directory as it is specific to the switcher tool.

### Fixed
- Performance issue in `focusrite_switcher.py` where sending routing commands took a long time due to waiting for
  server responses that were not always sent.
- Prevented `focusrite_switcher.py` from overwriting `~` (null) values and missing keys in `config.yml` with defaults.
- Fixed configuration path resolution in `focusrite_switcher.py` to correctly locate files when imported or launched
  from different directories.

### Added
- Successfully initialized `.venv` using `virtualenv` and installed Linux-compatible dependencies (`PyYAML`,
  `PyInstaller`).

### Changed
- Made `pywin32` and `pyinstaller` optional dependencies in `requirements.txt`, only installing them on Windows.
- Updated `install.py` to gracefully skip Windows-specific steps (Task Scheduler registration) when `pywin32` is not
  installed.

### Changed
- Switched recommendation for Debian-based systems from `python3-virtualenv` to `python3-venv` for better standard
  library alignment.
- Recommendation to install `python3-venv` globally on Debian-based systems to simplify virtual environment setup.
- Debian/Ubuntu specific setup instructions in `README.md`.

### Changed
- Renamed virtual environment directory from `venv` to `.venv` for better standard compliance.
- Updated `README.md` and `.gitignore` to reflect the new `.venv` directory name.

### Added
- Python virtual environment (`venv`) support for isolated dependency management.
- Detailed venv setup instructions in `README.md`.
- Updated technical specifications in project guidelines to recommend `venv`.
- Robust TCP communication: implemented clearing of the initial greeting buffer and waiting for server responses for
  each command, porting logic from `test_send_snapshot.py`.
- Caching of the last successful TCP port to `config.yml` to speed up future server discovery.
- `last_successful_port` configuration key under the `network` section.
- config.example.yml with default values.
- Default execution mode `playback_only` when no command-line arguments are provided.
- Added YAML configuration support via `config.yml`.
- Implemented automatic configuration creation with default values.
- Implemented intelligent configuration merging to restore missing keys from defaults while preserving user changes.
- Added `PyYAML` dependency to `requirements.txt`.
- Added platform-agnostic fallback for `win32gui` during testing and non-Windows environments.
- Created `CHANGELOG.md` to track project changes.
- Updated `.junie/guidelines.md` (now `AGENTS.md`): translated to English and added detailed "Development
  Principles" and "Technical Specifications" based on the existing codebase and README.

### Removed
- Removed temporary `get-pip.py` bootstrap script and accidentally created files.

### Changed
- Moved `config.yml` to `.gitignore` and added `config.example.yml` as a template.
- Renamed `.junie/guidelines.md` to `.junie/AGENTS.md`.
- Updated root `.gitignore` to use `/venv/` instead of `/.venv/` to match the project's virtual environment
  directory name.

### Fixed
- Resolved `ModuleNotFoundError: No module named 'yaml'` by ensuring `PyYAML` is installed in the environment.
