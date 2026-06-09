# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed `focusrite_switcher.py` failing to apply the `System Playback` routing-profile switch (while
  `8 Channel Analogue` worked). The real cause was the `network.timeout` value (used for the TCP port scan in
  `find_active_server_port()`) being too short at `0.02s`, which made server detection/connection unreliable.
  Raising it to `0.2s` in `config.default.yml` (and `config.yml`) resolves the issue.
- Fixed `focusrite_switcher.py` reporting `WARNING: No response received for command: ...` and appearing not to
  work even though the routing-profile switch was actually applied. A `<set>` command does not produce its own
  reply (the server applies it silently and only reflects the new value in its state dump), so the per-command
  "expect a response, otherwise warn" logic was a false alarm. The switcher now sends all commands without
  expecting per-command replies and confirms the result with a single trailing `<keep-alive/>` state read.
  Additionally, a routing-profile change (`<item id="6">`) can make the server briefly reset the connection
  while it reconfigures; this connection drop during the final confirmation is now tolerated instead of being
  logged as a fatal error and exiting.

### Added
- Documented two additional Focusrite Control Server behaviors in
  `docs/focusrite_control_api/focusrite_control_api.md`: a `<set>` command produces no per-command reply (the
  server applies it silently and only reflects the value in its state dump), and a routing-profile change
  (`<item id="6">`) briefly resets the connection while the server reconfigures.
- Added a `network.client_key` configuration option for the switcher tool (default `null` in
  `config.default.yml`). When the value is still `null`, `focusrite_switcher.py` auto-generates a random
  8-digit client key on startup and persists it to `config.yml` so the Focusrite Control approval stays stable.

### Changed
- Aligned `focusrite_switcher.py` with the reference script `focusrite_send_test.py` by sending all commands
  first and reading the server response only once at the end instead of after every command:
  `FocusriteClient.send_command()` no longer reads per command, a new public `FocusriteClient.receive()` method
  performs a single read, and `execute_commands()` sends every command and then reads once.
- Moved all Focusrite Control Server communication out of `focusrite_switcher.py` into a new reusable
  `tools/switcher/focusrite_client.py` module (`FocusriteClient`, `frame()`, `find_active_server_port()`).
- Updated `focusrite_switcher.py` to use the cleaned-up and fixed protocol via `focusrite_client.py`: correct
  6-digit uppercase hex length-prefix framing (no trailing newline), a `client-key` handshake, the mandatory
  `<device-subscribe devid="N" subscribe="true"/>` step before sending commands, and a warning when the server
  reports `authorised="false"` (client not yet approved in the Focusrite Control desktop application).
- `focusrite_send_test.py` was intentionally kept standalone and untouched as a simple one-file testing script.

### Added
- Documented how to switch the analogue input mode between `Line` and `Inst` via the `<mode>` element (e.g. id `799`
  for `Analogue 1`) in `docs/focusrite_control_api/focusrite_control_api.md`, including the selectable `<enum>` values
  and the `<set devid="1"><item id="799" value="..."/></set>` command syntax.
- Documented how to switch the routing profile (preset) via the `<preset>` element (id `6`) in
  `docs/focusrite_control_api/focusrite_control_api.md`, including the selectable `<enum>` values and the
  `<set devid="1"><item id="6" value="..."/></set>` command syntax.

### Fixed
- Identified the true reason `<set>` commands had no effect: a live test against a real Scarlett 18i8 server showed
  the server replies with `<approval ... authorised="false"/>`. While the client is not approved/trusted in the
  Focusrite Control desktop application, the server silently ignores every `<set>` (framing, `subscribe="true"`
  subscription and the `<set>`/`<item>` syntax were all already correct). Approval is bound to the `client-key`, so
  it only needs to be granted once. Updated `focusrite_send_test.py` to detect and warn on the approval status and
  documented the requirement in `docs/focusrite_control_api/focusrite_control_api.md`.
- Fixed `<set>` commands still being silently ignored by the Focusrite Control Server: the `<device-subscribe>`
  element requires the `subscribe="true"` attribute (`<device-subscribe devid="N" subscribe="true"/>`); a bare
  `<device-subscribe devid="N"/>` does not establish a real subscription, so all `<set>` commands were ignored.
  Confirmed against the authentic reverse-engineered client `raduvarga/Focusrite-Midi-Control` (`TCPListener.swift`).
  Also clarified that the `<set devid="N"><item id="X" value="V"/></set>` syntax is correct (no `<setvalue>` command
  exists). Updated `focusrite_send_test.py` and `docs/focusrite_control_api/focusrite_control_api.md` accordingly.
- Fixed `<set>` commands being silently ignored by the Focusrite Control Server. A client must now send
  `<device-subscribe>` after the handshake before any `<set>` command is accepted, and the `Length=XXXXXX `
  prefix must use 6-digit uppercase hexadecimal (no trailing newline). Updated `focusrite_send_test.py` and the
  "How to Control Input Volume (Gain)" section in `docs/focusrite_control_api/focusrite_control_api.md` accordingly.

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
