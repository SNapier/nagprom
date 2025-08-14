<?php
/**
 * NagProm Metrics Graphing Interface
 * 
 * Time series graphing for performance metrics with threshold monitoring
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
                'User-Agent: NagProm-Graph/1.0',
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

// Get URL parameters
$host = $_GET['host'] ?? '';
$service = $_GET['service'] ?? '';
$metric = $_GET['metric'] ?? '';
$time_range = $_GET['range'] ?? '30min';

// Validate required parameters
$error = '';
if (empty($host)) {
    $error = 'Host parameter is required';
} elseif (empty($service)) {
    $error = 'Service parameter is required';
}

// Calculate time range
$now = time();
$time_ranges = [
    '15min' => 15 * 60,
    '30min' => 30 * 60,
    '1hr' => 60 * 60,
    '6hr' => 6 * 60 * 60,
    '24hr' => 24 * 60 * 60,
    '7days' => 7 * 24 * 60 * 60
];

$selected_range_seconds = $time_ranges[$time_range] ?? $time_ranges['30min'];
$start_time = $now - $selected_range_seconds;
$end_time = $now;

// Format times for API
$start_iso = date('c', $start_time);
$end_iso = date('c', $end_time);

// Get time series data if parameters are valid
$time_series_data = [];
$thresholds_data = [];
$available_metrics = [];

if (empty($error)) {
    // Get thresholds for the service
    $thresholds_url = "$API_BASE/thresholds?host=" . urlencode($host);
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
            
            // Find the specific service thresholds
            foreach ($thresholds_data as $service_key => $service_thresholds) {
                if ($service_thresholds['service'] === $service) {
                    $thresholds_data = $service_thresholds['thresholds'] ?? [];
                    break;
                }
            }
        }
    }
    
    // Get time series data
    $timeseries_url = "$API_BASE/timeseries/performance?" . http_build_query([
        'host' => $host,
        'service' => $service,
        'start' => $start_iso,
        'end' => $end_iso,
        'step' => '5m'  // Increased step to reduce data points
    ]);
    
    $timeseries_result = makeRequest($timeseries_url, $TIMEOUT);
    
    if ($timeseries_result['success'] && $timeseries_result['http_code'] == 200) {
        $json_data = json_decode($timeseries_result['data'], true);
        if ($json_data && isset($json_data['success']) && $json_data['success'] && isset($json_data['data'])) {
            $time_series_data = $json_data['data'];
            
            // Extract available metrics from the timeseries data
            if (isset($time_series_data['timeseries']) && isset($time_series_data['timeseries']['result'])) {
                $available_metrics = [];
                $processed_data = [
                    'timestamps' => [],
                    'metrics' => []
                ];
                
                // Process each result from the timeseries
                foreach ($time_series_data['timeseries']['result'] as $result) {
                    if (isset($result['metric']['metric'])) {
                        $metric_name = $result['metric']['metric'];
                        $available_metrics[] = $metric_name;
                        
                        // Filter by specific metric if requested
                        if (empty($metric) || $metric === $metric_name) {
                            $metric_values = [];
                            $timestamps = [];
                            
                            // Extract timestamps and values
                            foreach ($result['values'] as $value_pair) {
                                $timestamps[] = $value_pair[0]; // Unix timestamp
                                $metric_values[] = floatval($value_pair[1]); // Metric value
                            }
                            
                            // Store the data
                            $processed_data['timestamps'] = $timestamps;
                            $processed_data['metrics'][$metric_name] = $metric_values;
                        }
                    }
                }
                
                // Update the data structure for the frontend
                $time_series_data = $processed_data;
                $available_metrics = array_unique($available_metrics);
            } else {
                $error = 'No time series data available for this service';
            }
        } else {
            $error = 'No time series data available for this service';
        }
    } else {
        $error = 'Failed to fetch time series data: ' . ($timeseries_result['error'] ?? 'Unknown error');
    }
}

// Get system information
$system_info = [
    'php_version' => phpversion(),
    'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown',
    'current_time' => date('Y-m-d H:i:s')
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NagProm Metrics Graph - <?php echo htmlspecialchars($service); ?></title>
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
        
        .controls-section {
            background: #3a3a3a;
            padding: 20px;
            border-bottom: 1px solid #4a4a4a;
        }
        
        .controls-form {
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
        
        .form-group select, .form-group input {
            padding: 8px 12px;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            background: #2d2d2d;
            color: #e0e0e0;
            font-size: 0.9em;
            min-width: 150px;
        }
        
        .control-button {
            background: #4299e1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
        }
        
        .control-button:hover {
            background: #3182ce;
        }
        
        .back-button {
            background: #e53e3e;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .back-button:hover {
            background: #c53030;
        }
        
        .error-message {
            background: #e53e3e;
            color: white;
            padding: 15px;
            border-radius: 4px;
            margin: 20px;
            text-align: center;
        }
        
        .graph-section {
            padding: 20px;
        }
        
        .graph-container {
            background: #3a3a3a;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #4a4a4a;
        }
        
        .graph-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .graph-title {
            font-size: 1.5em;
            font-weight: 600;
            color: #e0e0e0;
        }
        
        .graph-subtitle {
            color: #b0b0b0;
            font-size: 0.9em;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            width: 100%;
        }
        
        .metrics-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .summary-card {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #4a4a4a;
            text-align: center;
        }
        
        .summary-label {
            font-size: 0.8em;
            color: #b0b0b0;
            margin-bottom: 5px;
        }
        
        .summary-value {
            font-size: 1.2em;
            font-weight: 600;
            color: #4299e1;
        }
        
        .threshold-info {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #4a4a4a;
            margin-top: 20px;
        }
        
        .threshold-title {
            font-weight: 600;
            color: #e0e0e0;
            margin-bottom: 10px;
        }
        
        .threshold-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .threshold-label {
            color: #b0b0b0;
        }
        
        .threshold-value {
            color: #e0e0e0;
            font-weight: 500;
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
            <h1>NagProm Metrics Graph</h1>
            <p>Time series visualization for performance metrics</p>
        </div>
        
        <div class="navigation">
            <a href="index.php" class="nav-link primary">🏠 Dashboard Hub</a>
            <a href="metrics.php" class="nav-link">📊 Metrics Dashboard</a>
            <a href="debug.php" class="nav-link">Debug Info</a>
                         <a href="../../nagios/" class="nav-link">Back to Nagios</a>
        </div>
        
        <?php if (!empty($error)): ?>
        <div class="error-message">
            <strong>Error:</strong> <?php echo htmlspecialchars($error); ?>
        </div>
        <?php else: ?>
        
        <div class="controls-section">
            <form method="GET" class="controls-form">
                <input type="hidden" name="host" value="<?php echo htmlspecialchars($host); ?>">
                <input type="hidden" name="service" value="<?php echo htmlspecialchars($service); ?>">
                
                <div class="form-group">
                    <label for="range">Time Range:</label>
                    <select name="range" id="range" onchange="this.form.submit()">
                        <?php foreach ($time_ranges as $range_key => $range_seconds): ?>
                        <option value="<?php echo $range_key; ?>" <?php echo $time_range === $range_key ? 'selected' : ''; ?>>
                            <?php echo $range_key; ?>
                        </option>
                        <?php endforeach; ?>
                    </select>
                </div>
                
                <?php if (!empty($available_metrics) && count($available_metrics) > 1): ?>
                <div class="form-group">
                    <label for="metric">Filter Metric:</label>
                    <select name="metric" id="metric" onchange="this.form.submit()">
                        <option value="">All Metrics</option>
                        <?php foreach ($available_metrics as $metric_name): ?>
                        <option value="<?php echo htmlspecialchars($metric_name); ?>" <?php echo $metric === $metric_name ? 'selected' : ''; ?>>
                            <?php echo htmlspecialchars($metric_name); ?>
                        </option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <?php endif; ?>
                
                <div class="form-group">
                    <button type="submit" class="control-button">🔄 Refresh</button>
                </div>
                
                <div class="form-group">
                    <a href="metrics.php?host=<?php echo urlencode($host); ?>" class="back-button">← Back to Metrics</a>
                </div>
            </form>
        </div>
        
        <div class="graph-section">
            <div class="graph-container">
                <div class="graph-header">
                    <div>
                        <div class="graph-title"><?php echo htmlspecialchars($service); ?></div>
                        <div class="graph-subtitle">
                            Host: <?php echo htmlspecialchars($host); ?> | 
                            Time Range: <?php echo $time_range; ?> | 
                            Last Updated: <?php echo date('H:i:s'); ?>
                        </div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="metricsChart"></canvas>
                </div>
                
                                 <?php if (!empty($thresholds_data)): ?>
                 <div class="threshold-info">
                     <div class="threshold-title">Thresholds</div>
                     <?php 
                     // Only show thresholds for the selected metric (or first metric if none selected)
                     $selected_metric = $metric ?: (!empty($available_metrics) ? $available_metrics[0] : null);
                     if ($selected_metric && isset($thresholds_data[$selected_metric])): 
                         $threshold_values = $thresholds_data[$selected_metric];
                     ?>
                     <div class="threshold-item">
                         <span class="threshold-label"><?php echo htmlspecialchars($selected_metric); ?>:</span>
                         <span class="threshold-value">
                             <?php if (isset($threshold_values['warning'])): ?>
                             W: <?php echo htmlspecialchars($threshold_values['warning']); ?>
                             <?php endif; ?>
                             <?php if (isset($threshold_values['critical'])): ?>
                             | C: <?php echo htmlspecialchars($threshold_values['critical']); ?>
                             <?php endif; ?>
                         </span>
                     </div>
                     <?php else: ?>
                     <div class="threshold-item">
                         <span class="threshold-label">No thresholds available for selected metric</span>
                     </div>
                     <?php endif; ?>
                 </div>
                 <?php endif; ?>
            </div>
        </div>
        
        <?php endif; ?>
        
        <div class="footer">
            <p>NagProm Metrics Graph | Generated at <?php echo $system_info['current_time']; ?></p>
            <p>Time series visualization for performance monitoring and analysis.</p>
        </div>
    </div>
    
    <?php if (empty($error) && !empty($time_series_data)): ?>
    <script>
        // Prepare chart data
        const chartData = {
            labels: [],
            datasets: []
        };
        
        const thresholds = <?php echo json_encode($thresholds_data); ?>;
        const timeSeriesData = <?php echo json_encode($time_series_data); ?>;
        
        // Extract timestamps and create datasets
        if (timeSeriesData.timestamps && timeSeriesData.metrics) {
            // Create labels from timestamps
            chartData.labels = timeSeriesData.timestamps.map(timestamp => {
                const date = new Date(timestamp * 1000);
                return date.toLocaleTimeString();
            });
            
            // Create datasets for each metric
            const colors = ['#4299e1', '#48bb78', '#ed8936', '#f56565', '#9f7aea', '#38b2ac'];
            let colorIndex = 0;
            
            Object.keys(timeSeriesData.metrics).forEach(metricName => {
                const metricData = timeSeriesData.metrics[metricName];
                const dataset = {
                    label: metricName,
                    data: metricData,
                    borderColor: colors[colorIndex % colors.length],
                    backgroundColor: colors[colorIndex % colors.length] + '20',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                };
                
                chartData.datasets.push(dataset);
                colorIndex++;
            });
        }
        
        // Create the chart
        const ctx = document.getElementById('metricsChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#e0e0e0',
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#2d2d2d',
                        titleColor: '#e0e0e0',
                        bodyColor: '#e0e0e0',
                        borderColor: '#4a4a4a',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time',
                            color: '#e0e0e0'
                        },
                        ticks: {
                            color: '#b0b0b0'
                        },
                        grid: {
                            color: '#4a4a4a'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Value',
                            color: '#e0e0e0'
                        },
                        ticks: {
                            color: '#b0b0b0'
                        },
                        grid: {
                            color: '#4a4a4a'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
        
                 // Add threshold lines if available - only for selected metric
         if (thresholds && Object.keys(thresholds).length > 0) {
             // Get the currently selected metric (or first metric if none selected)
             const selectedMetric = '<?php echo htmlspecialchars($metric); ?>' || 
                                   (Object.keys(timeSeriesData.metrics).length > 0 ? Object.keys(timeSeriesData.metrics)[0] : null);
             
             if (selectedMetric && thresholds[selectedMetric]) {
                 const metricThresholds = thresholds[selectedMetric];
                 
                 if (metricThresholds.warning) {
                     chart.data.datasets.push({
                         label: `${selectedMetric} - Warning`,
                         data: Array(chartData.labels.length).fill(metricThresholds.warning),
                         borderColor: '#ed8936',
                         backgroundColor: 'transparent',
                         borderWidth: 1,
                         borderDash: [5, 5],
                         fill: false,
                         pointRadius: 0
                     });
                 }
                 
                 if (metricThresholds.critical) {
                     chart.data.datasets.push({
                         label: `${selectedMetric} - Critical`,
                         data: Array(chartData.labels.length).fill(metricThresholds.critical),
                         borderColor: '#f56565',
                         backgroundColor: 'transparent',
                         borderWidth: 1,
                         borderDash: [5, 5],
                         fill: false,
                         pointRadius: 0
                     });
                 }
             }
             
             chart.update();
         }
        
        // Auto-refresh every 60 seconds
        setTimeout(function() {
            location.reload();
        }, 60000);
    </script>
    <?php endif; ?>
</body>
</html>
