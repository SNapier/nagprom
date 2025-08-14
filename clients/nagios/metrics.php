<?php
/**
 * NagProm Performance Metrics Dashboard
 * 
 * Detailed performance metrics display with filtering and threshold gauges
 * Uses file_get_contents() instead of curl for compatibility
 */

// Configuration
$API_BASE = "http://127.0.0.1/nagprom/api/v1";
$TIMEOUT = 10; // seconds

// Helper function to make HTTP requests without curl
function makeRequest($url, $timeout = 10) {
    $context = stream_context_create([
        'http' => [
            'timeout' => $timeout,
            'method' => 'GET',
            'header' => [
                'User-Agent: NagProm-Metrics/1.0',
                'Accept: application/json',
                'Connection: close'
            ]
        ]
    ]);
    
    $response = @file_get_contents($url, false, $context);
    
    if ($response === false) {
        return [
            'success' => false,
            'error' => error_get_last()['message'] ?? 'Unknown error',
            'http_code' => 0
        ];
    }
    
    // Get HTTP response code
    $http_response_header = $http_response_header ?? [];
    $http_code = 200; // Default
    foreach ($http_response_header as $header) {
        if (preg_match('/^HTTP\/\d\.\d\s+(\d+)/', $header, $matches)) {
            $http_code = (int)$matches[1];
            break;
        }
    }
    
    return [
        'success' => true,
        'data' => $response,
        'http_code' => $http_code
    ];
}

// Get available hosts for filtering
$hosts_result = makeRequest("$API_BASE/hosts", $TIMEOUT);
$available_hosts = [];
$hosts_error = '';

if ($hosts_result['success'] && $hosts_result['http_code'] == 200) {
    $hosts_data = json_decode($hosts_result['data'], true);
    
    if ($hosts_data && isset($hosts_data['success']) && $hosts_data['success'] && isset($hosts_data['data'])) {
        $hosts_array = $hosts_data['data'];
        
        // Handle both paginated and direct array formats
        if (isset($hosts_array['hosts']) && is_array($hosts_array['hosts'])) {
            // Paginated format
            foreach ($hosts_array['hosts'] as $host) {
                if (isset($host['name']) && !empty($host['name'])) {
                    $available_hosts[] = $host['name'];
                }
            }
        } else if (is_array($hosts_array)) {
            // Direct array format
            foreach ($hosts_array as $host) {
                if (isset($host['name']) && !empty($host['name'])) {
                    $available_hosts[] = $host['name'];
                }
            }
        }
    } else {
        $hosts_error = 'Invalid hosts data structure received';
    }
} else {
    $hosts_error = $hosts_result['error'] ?? 'Failed to fetch hosts';
}

// Get selected host
$selected_host = $_GET['host'] ?? '';

// Get performance data and thresholds if host is selected
$performance_data = [];
$thresholds_data = [];
$metrics_error = '';
$thresholds_error = '';

if ($selected_host) {
    // Get performance metrics
    $metrics_url = "$API_BASE/metrics?host=" . urlencode($selected_host);
    $performance_result = makeRequest($metrics_url, $TIMEOUT);
    
    if ($performance_result['success'] && $performance_result['http_code'] == 200) {
        $json_data = json_decode($performance_result['data'], true);
        if ($json_data && isset($json_data['success']) && $json_data['success'] && isset($json_data['data'])) {
            $metrics_array = $json_data['data'];
            
            // Handle both paginated and direct array formats
            if (isset($metrics_array['metrics']) && is_array($metrics_array['metrics'])) {
                $performance_data = $metrics_array['metrics'];
            } else if (is_array($metrics_array)) {
                $performance_data = $metrics_array;
            }
        } else {
            $metrics_error = 'Invalid metrics data structure received';
        }
    } else {
        $metrics_error = $performance_result['error'] ?? 'Failed to fetch metrics';
    }
    
    // Get thresholds
    $thresholds_url = "$API_BASE/thresholds?host=" . urlencode($selected_host);
    $thresholds_result = makeRequest($thresholds_url, $TIMEOUT);
    
    if ($thresholds_result['success'] && $thresholds_result['http_code'] == 200) {
        $json_data = json_decode($thresholds_result['data'], true);
        if ($json_data && isset($json_data['success']) && $json_data['success'] && isset($json_data['data'])) {
            $thresholds_array = $json_data['data'];
            
            // Handle both paginated and direct array formats
            if (isset($thresholds_array['thresholds']) && is_array($thresholds_array['thresholds'])) {
                $thresholds_data = $thresholds_array['thresholds'];
            } else if (is_array($thresholds_array)) {
                $thresholds_data = $thresholds_array;
            }
        } else {
            $thresholds_error = 'Invalid thresholds data structure received';
        }
    } else {
        $thresholds_error = $thresholds_result['error'] ?? 'Failed to fetch thresholds';
    }
}

// Get system information
$system_info = [
    'php_version' => phpversion(),
    'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown',
    'current_time' => date('Y-m-d H:i:s'),
    'file_get_contents_available' => function_exists('file_get_contents'),
    'json_decode_available' => function_exists('json_decode')
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NagProm Performance Metrics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #2d2d2d;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .navigation {
            background: #3a3a3a;
            padding: 15px 20px;
            border-top: 1px solid #4a4a4a;
            text-align: center;
        }
        
        .nav-link {
            display: inline-block;
            margin: 0 10px;
            padding: 8px 16px;
            background: #4299e1;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
        }
        
        .nav-link:hover {
            background: #3182ce;
        }
        
        .nav-link.primary {
            background: #38a169;
        }
        
        .nav-link.primary:hover {
            background: #2f855a;
        }
        
        .filter-section {
            background: #3a3a3a;
            padding: 20px;
            border-bottom: 1px solid #4a4a4a;
        }
        
        .filter-form {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .form-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-group label {
            font-weight: 600;
            color: #e0e0e0;
            font-size: 0.9em;
            white-space: nowrap;
        }
        
        .form-group select {
            padding: 8px 12px;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            background: #2d2d2d;
            color: #e0e0e0;
            font-size: 0.9em;
            min-width: 200px;
        }
        
        .filter-button {
            background: #4299e1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
        }
        
        .filter-button:hover {
            background: #3182ce;
        }
        
        .clear-button {
            background: #e53e3e;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
        }
        
        .clear-button:hover {
            background: #c53030;
        }
        
        .filter-info {
            margin-top: 15px;
            padding: 10px;
            background: #2d2d2d;
            border-radius: 4px;
            font-size: 0.8em;
            color: #b0b0b0;
            border-left: 4px solid #4299e1;
        }
        
        .filter-info.error {
            border-left-color: #e53e3e;
            color: #feb2b2;
        }
        
        .metrics-section {
            padding: 20px;
        }
        
        .select-prompt, .no-data {
            text-align: center;
            padding: 40px;
            color: #b0b0b0;
        }
        
        .select-prompt h3, .no-data h3 {
            color: #e0e0e0;
            margin-bottom: 10px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .service-card {
            background: #3a3a3a;
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid #4a4a4a;
        }
        
        .service-header {
            background: #4a4a4a;
            padding: 15px;
            border-bottom: 1px solid #5a5a5a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .service-title {
            font-weight: 600;
            font-size: 1.2em;
            color: #e0e0e0;
        }
        
        .service-host {
            color: #b0b0b0;
            font-size: 0.9em;
        }
        
        .service-body {
            padding: 15px;
        }
        
        .metrics-grid-inner {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .metric-item {
            background: #2d2d2d;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #4299e1;
            border: 1px solid #4a4a4a;
        }
        
        .metric-name {
            font-weight: 600;
            color: #e0e0e0;
            font-size: 0.9em;
        }
        
        .metric-value {
            font-size: 1.1em;
            font-weight: 500;
            color: #4299e1;
        }
        
        .metric-unit {
            color: #b0b0b0;
            font-size: 0.8em;
        }
        
        .gauge-container {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #4a4a4a;
            text-align: center;
        }
        
        .gauge-title {
            font-weight: 600;
            color: #e0e0e0;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .gauge-canvas {
            max-width: 120px;
            max-height: 120px;
            margin: 0 auto 10px;
        }
        
        .gauge-value {
            font-size: 1.2em;
            font-weight: 600;
            color: #4299e1;
            margin-bottom: 5px;
        }
        
        .gauge-thresholds {
            font-size: 0.8em;
            color: #b0b0b0;
        }
        
        .refresh-button {
            background: #4299e1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            margin: 20px 0;
            transition: background-color 0.3s ease;
        }
        
        .refresh-button:hover {
            background: #3182ce;
        }
        
        .footer {
            background: #3a3a3a;
            padding: 20px;
            text-align: center;
            color: #b0b0b0;
            border-top: 1px solid #4a4a4a;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NagProm Performance Metrics</h1>
            <p>Detailed performance metrics with threshold monitoring</p>
        </div>
        
        <div class="navigation">
                         <a href="index.php" class="nav-link primary">🏠 Dashboard Hub</a>
             <a href="debug.php" class="nav-link">Debug Info</a>
             <a href="../../nagios/" class="nav-link">Back to Nagios</a>
        </div>
        
        <div class="filter-section">
            <form method="GET" class="filter-form">
                <div class="form-group">
                    <label for="host">Host:</label>
                    <select name="host" id="host">
                        <option value="">Choose Host...</option>
                        <?php if (!empty($available_hosts)): ?>
                        <?php foreach ($available_hosts as $host): ?>
                        <option value="<?php echo htmlspecialchars($host); ?>" <?php echo $selected_host === $host ? 'selected' : ''; ?>>
                            <?php echo htmlspecialchars($host); ?>
                        </option>
                        <?php endforeach; ?>
                        <?php else: ?>
                        <option value="" disabled>No hosts available</option>
                        <?php endif; ?>
                    </select>
                </div>
                
                <div class="form-group">
                    <button type="submit" class="filter-button">🔍 View Metrics</button>
                </div>
                
                <div class="form-group">
                    <a href="metrics.php" class="clear-button" style="text-decoration: none; text-align: center;">🗑️ Clear</a>
                </div>
            </form>
            
            <?php if ($hosts_error || $metrics_error || $thresholds_error): ?>
            <div class="filter-info error">
                <strong>Error:</strong>
                <?php if ($hosts_error): ?>
                <?php echo htmlspecialchars($hosts_error); ?>
                <?php endif; ?>
                <?php if ($hosts_error && ($metrics_error || $thresholds_error)): ?> | <?php endif; ?>
                <?php if ($metrics_error): ?>
                <?php echo htmlspecialchars($metrics_error); ?>
                <?php endif; ?>
                <?php if (($hosts_error || $metrics_error) && $thresholds_error): ?> | <?php endif; ?>
                <?php if ($thresholds_error): ?>
                <?php echo htmlspecialchars($thresholds_error); ?>
                <?php endif; ?>
            </div>
            <?php endif; ?>
        </div>
        
        <div class="metrics-section">
            <button class="refresh-button" onclick="location.reload()">🔄 Refresh Metrics</button>
            
            <?php if (empty($selected_host)): ?>
            <div class="select-prompt">
                <h3>Select a Host to View Performance Metrics</h3>
                <p>Choose a host from the dropdown above to view its performance metrics.</p>
            </div>
            <?php elseif (empty($performance_data)): ?>
            <div class="no-data">
                <h3>No Performance Data Available</h3>
                <p>The selected host returned no performance data.</p>
                <p>Try selecting a different host.</p>
            </div>
            <?php else: ?>
            <div class="metrics-grid">
                <?php foreach ($performance_data as $service_key => $service_data): ?>
                <div class="service-card">
                    <div class="service-header">
                        <div>
                            <div class="service-title"><?php echo htmlspecialchars($service_data['service']); ?></div>
                            <div class="service-host">Host: <?php echo htmlspecialchars($service_data['host']); ?></div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.8em; color: #b0b0b0;">
                                <?php echo date('H:i:s', $service_data['timestamp']); ?>
                            </div>
                            <div style="margin-top: 5px;">
                                <a href="graph.php?host=<?php echo urlencode($service_data['host']); ?>&service=<?php echo urlencode($service_data['service']); ?>" 
                                   style="color: #4299e1; text-decoration: none; font-size: 0.9em; font-weight: 500; padding: 4px 8px; border: 1px solid #4299e1; border-radius: 3px; background: rgba(66, 153, 225, 0.1);">
                                    📈 View Graph
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="service-body">
                        <?php if (isset($service_data['metrics']) && is_array($service_data['metrics'])): ?>
                        <div class="metrics-grid-inner">
                            <?php 
                            $service_thresholds = $thresholds_data[$service_key]['thresholds'] ?? [];
                            ?>
                            <?php foreach ($service_data['metrics'] as $metric_name => $metric_value): ?>
                            <?php 
                            $metric_thresholds = $service_thresholds[$metric_name] ?? null;
                            $metric_value_float = is_array($metric_value) ? floatval($metric_value['value']) : floatval($metric_value);
                            $metric_unit = is_array($metric_value) ? ($metric_value['unit'] ?? '') : '';
                            
                            // Determine if we should show as gauge (has thresholds) or regular metric
                            $show_as_gauge = $metric_thresholds && 
                                            (isset($metric_thresholds['warning']) || isset($metric_thresholds['critical'])) &&
                                            is_numeric($metric_value_float);
                            ?>
                            
                            <?php if ($show_as_gauge): ?>
                            <div class="gauge-container">
                                <div class="gauge-title"><?php echo htmlspecialchars($metric_name); ?></div>
                                <canvas id="gauge-<?php echo htmlspecialchars($service_key . '-' . $metric_name); ?>" class="gauge-canvas"></canvas>
                                <div class="gauge-value">
                                    <?php echo htmlspecialchars($metric_value_float); ?>
                                    <?php if ($metric_unit): ?>
                                    <span class="metric-unit"><?php echo htmlspecialchars($metric_unit); ?></span>
                                    <?php endif; ?>
                                </div>
                                <?php if ($metric_thresholds): ?>
                                <div class="gauge-thresholds">
                                    <?php if (isset($metric_thresholds['warning'])): ?>
                                    W: <?php echo htmlspecialchars($metric_thresholds['warning']); ?>
                                    <?php endif; ?>
                                    <?php if (isset($metric_thresholds['critical'])): ?>
                                    | C: <?php echo htmlspecialchars($metric_thresholds['critical']); ?>
                                    <?php endif; ?>
                                </div>
                                <?php endif; ?>
                            </div>
                            
                            <script>
                            (function() {
                                const ctx = document.getElementById('gauge-<?php echo htmlspecialchars($service_key . '-' . $metric_name); ?>').getContext('2d');
                                const value = <?php echo $metric_value_float; ?>;
                                const warning = <?php echo isset($metric_thresholds['warning']) ? $metric_thresholds['warning'] : 'null'; ?>;
                                const critical = <?php echo isset($metric_thresholds['critical']) ? $metric_thresholds['critical'] : 'null'; ?>;
                                
                                // Determine max value for gauge
                                let maxValue = Math.max(value, warning || 0, critical || 0) * 1.2;
                                if (maxValue <= 0) maxValue = 100;
                                
                                // Determine color based on thresholds
                                let color = '#48bb78'; // Green (OK)
                                if (critical && value >= critical) {
                                    color = '#f56565'; // Red (Critical)
                                } else if (warning && value >= warning) {
                                    color = '#ed8936'; // Orange (Warning)
                                }
                                
                                new Chart(ctx, {
                                    type: 'doughnut',
                                    data: {
                                        datasets: [{
                                            data: [value, maxValue - value],
                                            backgroundColor: [color, '#4a4a4a'],
                                            borderWidth: 0,
                                            cutout: '75%'
                                        }]
                                    },
                                    options: {
                                        responsive: true,
                                        maintainAspectRatio: true,
                                        plugins: {
                                            legend: { display: false },
                                            tooltip: { enabled: false }
                                        },
                                        animation: {
                                            animateRotate: true,
                                            duration: 1000
                                        }
                                    }
                                });
                            })();
                            </script>
                            
                            <?php else: ?>
                            <div class="metric-item">
                                <div class="metric-name"><?php echo htmlspecialchars($metric_name); ?></div>
                                <?php if (is_array($metric_value) && isset($metric_value['value'])): ?>
                                <div class="metric-value"><?php echo htmlspecialchars($metric_value['value']); ?></div>
                                <?php if (isset($metric_value['unit'])): ?>
                                <div class="metric-unit"><?php echo htmlspecialchars($metric_value['unit']); ?></div>
                                <?php endif; ?>
                                <?php else: ?>
                                <div class="metric-value"><?php echo htmlspecialchars($metric_value); ?></div>
                                <?php endif; ?>
                            </div>
                            <?php endif; ?>
                            <?php endforeach; ?>
                        </div>
                        <?php else: ?>
                        <div class="no-data">
                            <p>No metrics available for this service</p>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </div>
        
        <div class="footer">
            <p>NagProm Performance Metrics | Generated at <?php echo $system_info['current_time']; ?></p>
            <p>This dashboard displays detailed performance metrics with threshold monitoring.</p>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
        
        // Handle form submission
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('.filter-form');
            const hostSelect = document.getElementById('host');
            
            form.addEventListener('submit', function(e) {
                const selectedHost = hostSelect.value;
                if (!selectedHost) {
                    e.preventDefault();
                    alert('Please select a host first.');
                    return false;
                }
                // Form will submit normally and reload the page with the host parameter
            });
        });
    </script>
</body>
</html>
