# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Robust TCP communication: implemented clearing of the initial greeting buffer and waiting for server responses for each command, porting logic from `test_send_snapshot.py`.
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
- Updated `.junie/guidelines.md` (now `AGENTS.md`): translated to English and added detailed "Development Principles" and "Technical Specifications" based on the existing codebase and README.

### Changed
- Moved `config.yml` to `.gitignore` and added `config.example.yml` as a template.
- Renamed `.junie/guidelines.md` to `.junie/AGENTS.md`.

### Fixed
- Resolved `ModuleNotFoundError: No module named 'yaml'` by ensuring `PyYAML` is installed in the environment.
