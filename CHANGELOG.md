# Changelog

All notable changes to nagprom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-14-08
### Breaking Changes
- **Folder Structure Reorganization** - Complete restructuring for better organization:
  - `dashboards/` → `grafana-dashboards/` (Grafana-specific dashboards only)
  - `web/` → `clients/nagios/` (PHP dashboards moved to dedicated client directory)
  - `analytics/` directory added for ML and SRE components
  - `docs/` directory restructured with subdirectories for different documentation types
  - `api/` directory contains all API-related files and configuration
  - `core/` directory for core NagProm functionality
  - `assets/` directory for images and static resources

- **API Endpoint Changes** - REST API endpoints have been standardized:
  - All endpoints now use `/api/v1/` prefix
  - Authentication now uses `X-API-Key` header instead of query parameter
  - Response format standardized across all endpoints
  - Rate limiting applied to all endpoints

- **Configuration File Changes** - Configuration structure updated:
  - Apache configuration moved to `api/apache-nagprom.conf`
  - Installation scripts consolidated in `api/` directory
  - Service files updated for new directory structure

### Added
- **🔍 Alert Correlation Engine** - Machine learning-powered alert correlation system:
  - Multi-dimensional correlation (temporal, spatial, similarity, dependency-based)
  - DBSCAN clustering and TF-IDF similarity analysis
  - Pattern recognition and noise reduction
  - Root cause analysis with automated suggestions
  - Predictive alerting based on historical patterns
  - Incident timeline reconstruction
  - Alert fatigue reduction

- **📊 SRE Analytics Engine** - Comprehensive Site Reliability Engineering features:
  - Service Level Objectives (SLO) management and tracking
  - Error budget monitoring with burn rate analysis
  - Reliability metrics: MTTR, MTBF, availability percentages
  - Capacity planning insights and trend analysis
  - Anomaly detection using statistical analysis
  - Business impact analysis with revenue impact calculations
  - Service dependency mapping and analysis

- **🌐 Complete REST API** - Full-featured REST API for Nagios monitoring data:
  - Prometheus integration with query and query_range support
  - Embedded SRE analytics within main API service
  - Time-series data support for historical analysis
  - Rate limiting and authentication
  - Webhook support for alert integration

- **📱 PHP Dashboard Suite** - Complete web interface including:
  - Main dashboard hub (`index.php`)
  - Performance metrics dashboard (`metrics.php`) with gauge displays
  - Debug information dashboard (`debug.php`)
  - Time-series graphing interface (`graph.php`) with threshold visualization
  - SRE analytics dashboard (`sre_analytics.php`)

- **🔒 Security & Performance**:
  - API Key Authentication (optional)
  - Rate limiting and pagination
  - CORS configuration for web access
  - Input validation and sanitization
  - Error handling without information leakage

- **📚 Comprehensive Documentation**:
  - Technical API guides with OpenAPI/Swagger support
  - SRE analytics user guides
  - Production deployment documentation
  - Integration examples and tutorials

### Changed
- **Improved Data Processing** - Better handling of Nagios performance data and thresholds
- **Modern Web Interface** - Responsive PHP dashboards with Chart.js integration
- **Production-Ready Installation** - Automated installers with systemd service integration
- **Apache Integration** - Reverse proxy configuration for secure external access

### Fixed
- Performance data parsing and threshold extraction
- Prometheus query compatibility and error handling
- **Installer Scripts** - Fixed corrupted installer scripts that were causing "required file not found" errors
- **API Import Issues** - Resolved analytics engine import problems with proper path resolution
- **Dashboard Styling** - Fixed correlation dashboard to match dark theme and removed incorrect navigation links
- **Dependency Management** - Improved graceful fallbacks for missing ML libraries
- **Path Resolution** - Fixed analytics engine path issues in production installations

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