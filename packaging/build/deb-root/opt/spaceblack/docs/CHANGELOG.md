# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-   **Modular Skills System**: Extensible architecture for adding new capabilities.
-   **Telegram Integration**: Full rewrite of the Telegram Bot Gateway (`tools/skills/telegram/bot.py`).
-   **OpenWeather Integration**: New skill for real-time weather data (`tools/skills/openweather/weather.py`).
-   **Setup Wizard**: Automated onboarding script (`setup_wizard.py`) linked to `main.py`.
-   **Documentation**: Comprehensive updates to `docs/` covering Tools, Skills, Memory, and Security.

### Changed
-   **Configuration**: Centralized configuration in `config.json`.
-   **TUI**: Improved UI/UX for Skills and Config screens (Radio buttons, better styling).
-   **Project Structure**: Moved `telegram_bot.py` to `tools/skills/`. Removed redundant `agent_logic.py`.
-   **Agent Logic**: Updated `agent.py` to dynamically load enabled skills.

### Fixed
-   **Start Issues**: Resolved crashes related to missing `config.json` on fresh installs.
-   **Import Errors**: Fixed path issues in `bot.py` and test scripts.
