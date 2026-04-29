# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- **SOC Coordinator (PI-5)**: Upgraded `test_flexible_command.py` into a complete functional E2E test that validates the MQTT communication loop and feedback generation.

### Changed
- **SOC Sensor (PI-4)**: Modified `agente_monitor.py` to publish STDOUT, STDERR, and execution results back to the `comandos/<sensor>/out` MQTT topic, closing the feedback loop required for autonomous agent triage.

