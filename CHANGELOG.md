# Changelog

All notable changes to nagprom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-03-08

### Breaking Changes
- Standardized metric names (old format no longer supported)
  - Old: `{host}_{service}_state` → New: `nagios_service_state`
  - Old: `{host}_{service}` → New: `nagios_performance_data`
- Restructured label format for all metrics
  - Added consistent labeling scheme across all metrics
  - Changed label names to be more descriptive and standardized

### Added
- **New Grafana Dashboards**
  - Host Status Overview dashboard
    - Quick stats with zero-value display
    - Status history timeline
    - Problem hosts panel
    - Status distribution chart
    - Hierarchical host status view
  - Service Status Overview dashboard
    - Summary statistics
    - Service status history
    - Critical & warning services panel
    - Service distribution chart
    - Hierarchical service view
  - Service Monitoring Detail dashboard
    - Performance metrics over time
    - State history tracking
    - Warning/critical thresholds display
    - URL parameter support for linking

- **Enhanced Metric Structure**
  - Service state tracking with detailed labels
  - Performance threshold metrics
  - Timestamp tracking for all checks
  - Host and service metadata metrics

- **Documentation**
  - Dashboard usage guide
  - Troubleshooting documentation
  - PromQL query examples
  - Installation and upgrade instructions

### Changed
- **Performance Data Processing**
  - Improved parsing for complex performance data
  - Added support for multiple metrics per check
  - Enhanced threshold extraction and tracking
  - Added unit validation and standardization

- **Error Handling**
  - Added graceful parsing of malformed data
  - Improved error reporting
  - Added directory creation checks
  - Enhanced permission validation

### Fixed
- Metric name consistency issues
- Performance data parsing edge cases
- Directory permission handling
- State mapping inconsistencies

## [0.0.5] - 2024-02-15

### Added
- Basic threshold support in metrics
- Warning and critical threshold extraction
- Unit of measurement parsing

### Changed
- Enhanced metric formatting
- Improved error handling for malformed data
- Better performance data parsing

## [0.0.4] - 2024-01-20

### Added
- Basic service state monitoring
- Simple performance data collection
- Initial metric export functionality

### Changed
- Improved metric file handling
- Enhanced command-line argument parsing

## [0.0.1] - 2024-01-10

### Added
- Initial release
- Basic host state monitoring
- Simple metric file generation
- Command-line interface