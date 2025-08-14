<?php
/**
 * NagProm Debug Dashboard
 * 
 * Debug information and system status
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
                'User-Agent: NagProm-Debug/1.0',
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

// Only fetch debug data if user clicked the run button
$debug_data = [];
$debug_run = false;

if (isset($_GET['run_debug']) && $_GET['run_debug'] === '1') {
    $debug_run = true;
    
    // Get debug data with limits
    $debug_result = makeRequest("$API_BASE/debug/metrics", $TIMEOUT);
    
    if ($debug_result['success'] && $debug_result['http_code'] == 200) {
        $json_data = json_decode($debug_result['data'], true);
        if ($json_data && isset($json_data['data'])) {
            $debug_data = $json_data['data'];
            
            // Limit sample data to prevent large datasets
            if (isset($debug_data['processed_hosts']) && is_array($debug_data['processed_hosts'])) {
                $debug_data['processed_hosts'] = array_slice($debug_data['processed_hosts'], 0, 10);
            }
            
            if (isset($debug_data['processed_services']) && is_array($debug_data['processed_services'])) {
                $debug_data['processed_services'] = array_slice($debug_data['processed_services'], 0, 25);
            }
            
            if (isset($debug_data['processed_performance']) && is_array($debug_data['processed_performance'])) {
                $debug_data['processed_performance'] = array_slice($debug_data['processed_performance'], 0, 25);
            }
        }
    }
    
    // Get thresholds debug data for localhost only
    $thresholds_debug_result = makeRequest("$API_BASE/thresholds?host=localhost", $TIMEOUT);
    
    if ($thresholds_debug_result['success'] && $thresholds_debug_result['http_code'] == 200) {
        $thresholds_json_data = json_decode($thresholds_debug_result['data'], true);
        if ($thresholds_json_data && isset($thresholds_json_data['success']) && $thresholds_json_data['success'] && isset($thresholds_json_data['data'])) {
            $thresholds_array = $thresholds_json_data['data'];
            
            // Handle both paginated and direct array formats
            if (isset($thresholds_array['thresholds']) && is_array($thresholds_array['thresholds'])) {
                $thresholds_debug_data = $thresholds_array['thresholds'];
            } else if (is_array($thresholds_array)) {
                $thresholds_debug_data = $thresholds_array;
            } else {
                $thresholds_debug_data = [];
            }
            
            // Limit to first 10 services for debugging
            $thresholds_debug_data = array_slice($thresholds_debug_data, 0, 10, true);
        } else {
            $thresholds_debug_data = [];
        }
    } else {
        $thresholds_debug_data = [];
    }
}

// Get system information
$system_info = [
    'php_version' => phpversion(),
    'server_software' => $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown',
    'server_name' => $_SERVER['SERVER_NAME'] ?? 'Unknown',
    'document_root' => $_SERVER['DOCUMENT_ROOT'] ?? 'Unknown',
    'current_time' => date('Y-m-d H:i:s'),
    'file_get_contents_available' => function_exists('file_get_contents'),
    'json_decode_available' => function_exists('json_decode'),
    'curl_available' => function_exists('curl_init'),
    'memory_limit' => ini_get('memory_limit'),
    'max_execution_time' => ini_get('max_execution_time'),
    'allow_url_fopen' => ini_get('allow_url_fopen') ? 'On' : 'Off'
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NagProm Debug Dashboard</title>
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
            background: linear-gradient(135deg, #805ad5 0%, #553c9a 100%);
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
        
        .content {
            padding: 20px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #e0e0e0;
            border-bottom: 2px solid #4a4a4a;
            padding-bottom: 10px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .info-card {
            background: #3a3a3a;
            border: 1px solid #4a4a4a;
            border-radius: 6px;
            padding: 20px;
        }
        
        .info-card h3 {
            margin: 0 0 15px 0;
            color: #e0e0e0;
            font-size: 1.2em;
        }
        
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #4a4a4a;
        }
        
        .info-item:last-child {
            border-bottom: none;
        }
        
        .info-label {
            font-weight: 600;
            color: #b0b0b0;
        }
        
        .info-value {
            color: #e0e0e0;
            font-family: monospace;
        }
        
        .success { color: #48bb78; }
        .warning { color: #ed8936; }
        .error { color: #f56565; }
        
        .data-section {
            background: #3a3a3a;
            border: 1px solid #4a4a4a;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .data-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #e0e0e0;
        }
        
        .data-content {
            background: #2d2d2d;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            color: #e0e0e0;
        }
        
        .run-button {
            background: #48bb78;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.1em;
            margin: 20px 0;
            transition: background-color 0.3s ease;
            font-weight: 600;
        }
        
        .run-button:hover {
            background: #38a169;
        }
        
        .run-button:disabled {
            background: #6c757d;
            cursor: not-allowed;
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
            background: #48bb78;
        }
        
        .nav-link.primary:hover {
            background: #38a169;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-ok { background-color: #48bb78; }
        .status-warning { background-color: #ed8936; }
        .status-error { background-color: #f56565; }
        
        .welcome-message {
            background: #4a4a4a;
            padding: 30px;
            border-radius: 6px;
            text-align: center;
            margin: 20px 0;
        }
        
        .welcome-message h3 {
            margin: 0 0 15px 0;
            color: #e0e0e0;
            font-size: 1.5em;
        }
        
        .welcome-message p {
            margin: 0 0 20px 0;
            color: #b0b0b0;
            font-size: 1.1em;
        }
        
        .data-limits {
            background: #4a4a4a;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 0.9em;
            color: #e0e0e0;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NagProm Debug Dashboard</h1>
            <p>System information and debug data</p>
        </div>
        
        <div class="navigation">
                         <a href="index.php" class="nav-link primary">🏠 Dashboard Hub</a>
             <a href="metrics.php" class="nav-link">Performance Metrics</a>
             <a href="../../nagios/" class="nav-link">Back to Nagios</a>
        </div>
        
        <div class="content">
            <button class="refresh-button" onclick="location.reload()">🔄 Refresh Debug Info</button>
            
            <div class="section">
                <div class="section-title">System Information</div>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>PHP Configuration</h3>
                        <div class="info-item">
                            <span class="info-label">PHP Version:</span>
                            <span class="info-value"><?php echo $system_info['php_version']; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Memory Limit:</span>
                            <span class="info-value"><?php echo $system_info['memory_limit']; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Max Execution Time:</span>
                            <span class="info-value"><?php echo $system_info['max_execution_time']; ?>s</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">allow_url_fopen:</span>
                            <span class="info-value"><?php echo $system_info['allow_url_fopen']; ?></span>
                        </div>
                    </div>
                    
                    <div class="info-card">
                        <h3>Server Information</h3>
                        <div class="info-item">
                            <span class="info-label">Server Software:</span>
                            <span class="info-value"><?php echo $system_info['server_software']; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Server Name:</span>
                            <span class="info-value"><?php echo $system_info['server_name']; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Document Root:</span>
                            <span class="info-value"><?php echo $system_info['document_root']; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Current Time:</span>
                            <span class="info-value"><?php echo $system_info['current_time']; ?></span>
                        </div>
                    </div>
                    
                    <div class="info-card">
                        <h3>PHP Extensions</h3>
                        <div class="info-item">
                            <span class="info-label">file_get_contents:</span>
                            <span class="info-value">
                                <span class="status-indicator <?php echo $system_info['file_get_contents_available'] ? 'status-ok' : 'status-error'; ?>"></span>
                                <?php echo $system_info['file_get_contents_available'] ? 'Available' : 'Not Available'; ?>
                            </span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">JSON Support:</span>
                            <span class="info-value">
                                <span class="status-indicator <?php echo $system_info['json_decode_available'] ? 'status-ok' : 'status-error'; ?>"></span>
                                <?php echo $system_info['json_decode_available'] ? 'Available' : 'Not Available'; ?>
                            </span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">cURL Support:</span>
                            <span class="info-value">
                                <span class="status-indicator <?php echo $system_info['curl_available'] ? 'status-ok' : 'status-warning'; ?>"></span>
                                <?php echo $system_info['curl_available'] ? 'Available' : 'Not Available'; ?>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            
            <?php if (!$debug_run): ?>
            <div class="welcome-message">
                <h3>Ready to Fetch Debug Data</h3>
                <p>Click the button below to fetch debug information from the NagProm API.</p>
                <p>This will retrieve sample data to help diagnose API connectivity and data structure.</p>
                <div class="data-limits">
                    <strong>Data Limits:</strong> 10 hosts, 25 services, 25 metrics, 10 services with thresholds (to prevent large datasets)
                </div>
                <a href="?run_debug=1" class="run-button">🔍 Fetch Debug Data</a>
            </div>
            <?php else: ?>
            <div style="display: flex; gap: 10px; margin: 20px 0;">
                <a href="?run_debug=1" class="run-button">🔄 Fetch Again</a>
                <button class="refresh-button" onclick="location.reload()">🔄 Refresh Page</button>
            </div>
            <?php endif; ?>
            
            <?php if (!empty($debug_data)): ?>
            <div class="section">
                <div class="section-title">API Debug Information</div>
                
                <div class="info-grid">
                    <div class="info-card">
                        <h3>Prometheus Connection</h3>
                        <div class="info-item">
                            <span class="info-label">Prometheus URL:</span>
                            <span class="info-value"><?php echo $debug_data['prometheus_url'] ?? 'Unknown'; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Total Metrics:</span>
                            <span class="info-value"><?php echo $debug_data['total_metrics'] ?? 0; ?></span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Nagios Metrics:</span>
                            <span class="info-value"><?php echo count($debug_data['nagios_metrics'] ?? []); ?></span>
                        </div>
                    </div>
                    
                    <div class="info-card">
                        <h3>Processed Data (Limited)</h3>
                        <div class="info-item">
                            <span class="info-label">Hosts Found:</span>
                            <span class="info-value"><?php echo count($debug_data['processed_hosts'] ?? []); ?> (max 10)</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Services Found:</span>
                            <span class="info-value"><?php echo count($debug_data['processed_services'] ?? []); ?> (max 25)</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Performance Data:</span>
                            <span class="info-value"><?php echo count($debug_data['processed_performance'] ?? []); ?> (max 25)</span>
                        </div>
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="data-title">Available Nagios Metrics</div>
                    <div class="data-content"><?php echo htmlspecialchars(json_encode($debug_data['nagios_metrics'] ?? [], JSON_PRETTY_PRINT)); ?></div>
                </div>
                
                <div class="data-section">
                    <div class="data-title">Sample Host Data (Limited to 10)</div>
                    <div class="data-content"><?php echo htmlspecialchars(json_encode($debug_data['sample_host_data'] ?? [], JSON_PRETTY_PRINT)); ?></div>
                </div>
                
                <div class="data-section">
                    <div class="data-title">Sample Service Data (Limited to 25)</div>
                    <div class="data-content"><?php echo htmlspecialchars(json_encode($debug_data['sample_service_data'] ?? [], JSON_PRETTY_PRINT)); ?></div>
                </div>
                
                <div class="data-section">
                    <div class="data-title">Sample Performance Data (Limited to 25)</div>
                    <div class="data-content"><?php echo htmlspecialchars(json_encode($debug_data['sample_performance_data'] ?? [], JSON_PRETTY_PRINT)); ?></div>
                </div>
                
                <?php if (isset($thresholds_debug_data) && !empty($thresholds_debug_data)): ?>
                <div class="section">
                    <div class="section-title">Localhost Thresholds Debug Information</div>
                    
                    <div class="info-grid">
                        <div class="info-card">
                            <h3>Localhost Thresholds Summary</h3>
                            <div class="info-item">
                                <span class="info-label">Services with Thresholds:</span>
                                <span class="info-value"><?php echo count($thresholds_debug_data); ?></span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">API Status:</span>
                                <span class="info-value">
                                    <span class="status-indicator status-success"></span>
                                    Success (HTTP <?php echo $thresholds_debug_result['http_code']; ?>)
                                </span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Data Source:</span>
                                <span class="info-value">localhost services only</span>
                            </div>
                        </div>
                        
                        <div class="info-card">
                            <h3>Sample Services</h3>
                            <?php 
                            $sample_count = 0;
                            foreach ($thresholds_debug_data as $service_key => $service_data): 
                                if ($sample_count >= 5) break;
                                $sample_count++;
                            ?>
                            <div class="info-item">
                                <span class="info-label"><?php echo htmlspecialchars($service_data['service']); ?>:</span>
                                <span class="info-value"><?php echo count($service_data['thresholds']); ?> metrics</span>
                            </div>
                            <?php endforeach; ?>
                            <?php if (count($thresholds_debug_data) > 5): ?>
                            <div class="info-item">
                                <span class="info-label">And <?php echo count($thresholds_debug_data) - 5; ?> more...</span>
                                <span class="info-value"></span>
                            </div>
                            <?php endif; ?>
                        </div>
                    </div>
                    
                    <div class="data-section">
                        <div class="data-title">Localhost Thresholds Data (First 10 services)</div>
                        <div class="data-content"><?php echo htmlspecialchars(json_encode($thresholds_debug_data, JSON_PRETTY_PRINT)); ?></div>
                    </div>
                </div>
                <?php elseif (isset($thresholds_debug_data) && empty($thresholds_debug_data)): ?>
                <div class="section">
                    <div class="section-title">Localhost Thresholds Debug Information</div>
                    
                    <div class="info-card">
                        <h3>No Thresholds Found</h3>
                        <div class="info-item">
                            <span class="info-label">API Status:</span>
                            <span class="info-value">
                                <?php if ($thresholds_debug_result['success']): ?>
                                <span class="status-indicator status-success"></span>
                                Success (HTTP <?php echo $thresholds_debug_result['http_code']; ?>)
                                <?php else: ?>
                                <span class="status-indicator status-error"></span>
                                Failed (HTTP <?php echo $thresholds_debug_result['http_code']; ?>)
                                <?php endif; ?>
                            </span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Result:</span>
                            <span class="info-value">No thresholds found for localhost services</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Error:</span>
                            <span class="info-value"><?php echo $thresholds_debug_result['error'] ?? 'None'; ?></span>
                        </div>
                    </div>
                </div>
                <?php endif; ?>
            </div>
            <?php elseif ($debug_run): ?>
            <div class="section">
                <div class="section-title">API Debug Information</div>
                <div class="info-card">
                    <h3>Connection Status</h3>
                    <div class="info-item">
                        <span class="info-label">API Status:</span>
                        <span class="info-value">
                            <span class="status-indicator status-error"></span>
                            Failed to connect to API
                        </span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Error:</span>
                        <span class="info-value"><?php echo $debug_result['error'] ?? 'Unknown error'; ?></span>
                    </div>
                </div>
            </div>
            <?php endif; ?>
        </div>
        
        <div class="footer">
            <p>NagProm Debug Dashboard | Generated at <?php echo $system_info['current_time']; ?></p>
            <p>This dashboard provides detailed debug information about the NagProm API and system configuration.</p>
        </div>
    </div>
</body>
</html>
