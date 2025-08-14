<?php
/**
 * NagProm API Dashboard
 * 
 * Comprehensive API endpoint testing and monitoring dashboard
 * Uses file_get_contents() instead of curl for compatibility
 */

// Configuration
$API_BASE = "http://127.0.0.1/nagprom/api/v1";
$TIMEOUT = 10; // seconds
$MAX_RESPONSE_SIZE = 50000; // 50KB limit to prevent large datasets

// Helper function to make HTTP requests without curl
function makeRequest($url, $timeout = 10) {
    $context = stream_context_create([
        'http' => [
            'timeout' => $timeout,
            'method' => 'GET',
            'header' => [
                'User-Agent: NagProm-Dashboard/1.0',
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

// Helper function to format response time
function formatTime($seconds) {
    if ($seconds < 1) {
        return round($seconds * 1000, 2) . 'ms';
    }
    return round($seconds, 2) . 's';
}

// Helper function to get status icon
function getStatusIcon($success, $http_code = 0) {
    if (!$success) {
        return '❌';
    }
    if ($http_code >= 200 && $http_code < 300) {
        return '✅';
    }
    if ($http_code >= 400 && $http_code < 500) {
        return '⚠️';
    }
    return '❌';
}

// Helper function to get status class
function getStatusClass($success, $http_code = 0) {
    if (!$success) {
        return 'error';
    }
    if ($http_code >= 200 && $http_code < 300) {
        return 'success';
    }
    if ($http_code >= 400 && $http_code < 500) {
        return 'warning';
    }
    return 'error';
}

// Helper function to truncate large responses
function truncateResponse($data, $maxSize = 50000) {
    if (strlen($data) > $maxSize) {
        return substr($data, 0, $maxSize) . "\n\n... (truncated - response too large)";
    }
    return $data;
}

// Test all endpoints
$tests = [
    'health' => [
        'name' => 'Health Check',
        'url' => "$API_BASE/health",
        'description' => 'Basic API health status and Prometheus connectivity'
    ],
    'summary' => [
        'name' => 'Summary',
        'url' => "$API_BASE/summary",
        'description' => 'Monitoring summary with host/service counts and states'
    ],
    'hosts' => [
        'name' => 'Hosts',
        'url' => "$API_BASE/hosts",
        'description' => 'All monitored hosts with states'
    ],
    'services' => [
        'name' => 'Services',
        'url' => "$API_BASE/services",
        'description' => 'All monitored services with states'
    ],
    'sre_dashboard' => [
        'name' => 'SRE Dashboard',
        'url' => "$API_BASE/sre/dashboard",
        'description' => 'SRE analytics with uptime percentages'
    ],
    'sre_capacity' => [
        'name' => 'SRE Capacity',
        'url' => "$API_BASE/sre/capacity",
        'description' => 'Capacity planning and recommendations'
    ],
    'performance' => [
        'name' => 'Performance',
        'url' => "$API_BASE/performance",
        'description' => 'Performance metrics with service data'
    ],
    'metrics' => [
        'name' => 'Raw Metrics',
        'url' => "$API_BASE/metrics",
        'description' => 'Raw performance data for all services'
    ]
];

// Initialize results array
$results = [];
$total_tests = count($tests);
$passed_tests = 0;
$total_time = 0;
$success_rate = 0;

// Check if individual test was requested
$individual_test = $_GET['test'] ?? '';
$run_all_tests = isset($_GET['run_tests']) && $_GET['run_tests'] === '1';

if ($individual_test && isset($tests[$individual_test])) {
    // Run single test
    $test = $tests[$individual_test];
    $start_time = microtime(true);
    $result = makeRequest($test['url'], $TIMEOUT);
    $test_time = microtime(true) - $start_time;
    
    $result['test_time'] = $test_time;
    $result['test_name'] = $test['name'];
    $result['test_description'] = $test['description'];
    $result['test_url'] = $test['url'];
    
    if ($result['success'] && $result['http_code'] >= 200 && $result['http_code'] < 300) {
        $passed_tests = 1;
        
        // Try to parse JSON response and truncate if needed
        $json_data = json_decode($result['data'], true);
        if ($json_data !== null) {
            $result['parsed_data'] = $json_data;
            $result['data'] = truncateResponse(json_encode($json_data, JSON_PRETTY_PRINT), $MAX_RESPONSE_SIZE);
        } else {
            $result['data'] = truncateResponse($result['data'], $MAX_RESPONSE_SIZE);
        }
    }
    
    $results[$individual_test] = $result;
    $total_time = $test_time;
    $success_rate = ($passed_tests / 1) * 100;
    
} elseif ($run_all_tests) {
    // Run all tests
    $start_time = microtime(true);
    
    foreach ($tests as $key => $test) {
        $test_start = microtime(true);
        $result = makeRequest($test['url'], $TIMEOUT);
        $test_time = microtime(true) - $test_start;
        
        $result['test_time'] = $test_time;
        $result['test_name'] = $test['name'];
        $result['test_description'] = $test['description'];
        $result['test_url'] = $test['url'];
        
        if ($result['success'] && $result['http_code'] >= 200 && $result['http_code'] < 300) {
            $passed_tests++;
            
            // Try to parse JSON response and truncate if needed
            $json_data = json_decode($result['data'], true);
            if ($json_data !== null) {
                $result['parsed_data'] = $json_data;
                $result['data'] = truncateResponse(json_encode($json_data, JSON_PRETTY_PRINT), $MAX_RESPONSE_SIZE);
            } else {
                $result['data'] = truncateResponse($result['data'], $MAX_RESPONSE_SIZE);
            }
        }
        
        $results[$key] = $result;
    }
    
    $total_time = microtime(true) - $start_time;
    $success_rate = ($passed_tests / $total_tests) * 100;
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
    'curl_available' => function_exists('curl_init')
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NagProm API Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #2d2d2d;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
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
        
        .summary {
            background: #3a3a3a;
            padding: 20px;
            border-bottom: 1px solid #4a4a4a;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            border: 1px solid #4a4a4a;
        }
        
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 2em;
            font-weight: 300;
        }
        
        .summary-card p {
            margin: 0;
            color: #b0b0b0;
            font-size: 0.9em;
        }
        
        .success { color: #48bb78; }
        .warning { color: #ed8936; }
        .error { color: #f56565; }
        
        .system-info {
            background: #4a4a4a;
            padding: 15px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.9em;
            color: #e0e0e0;
        }
        
        .tests-section {
            padding: 20px;
        }
        
        .test-grid {
            display: grid;
            gap: 15px;
        }
        
        .test-card {
            border: 1px solid #4a4a4a;
            border-radius: 6px;
            overflow: hidden;
            background: #2d2d2d;
        }
        
        .test-header {
            padding: 15px;
            background: #3a3a3a;
            border-bottom: 1px solid #4a4a4a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .test-title {
            font-weight: 600;
            font-size: 1.1em;
            color: #e0e0e0;
        }
        
        .test-status {
            font-size: 1.5em;
        }
        
        .test-body {
            padding: 15px;
        }
        
        .test-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .detail-item {
            background: #3a3a3a;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            border: 1px solid #4a4a4a;
        }
        
        .detail-label {
            font-weight: 600;
            color: #b0b0b0;
        }
        
        .test-response {
            background: #3a3a3a;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85em;
            white-space: pre-wrap;
            cursor: pointer;
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
        
        .test-button {
            background: #4299e1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.3s ease;
            margin: 5px;
        }
        
        .test-button:hover {
            background: #3182ce;
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
        
        .test-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        
        .data-warning {
            background: #ed8936;
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            margin: 10px 0;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .test-details {
                grid-template-columns: 1fr;
            }
            
            .test-buttons {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>NagProm API Dashboard</h1>
            <p>Comprehensive monitoring and API endpoint testing</p>
        </div>
        
        <div class="navigation">
            <a href="index.php" class="nav-link primary">🏠 Dashboard Hub</a>
            <a href="metrics.php" class="nav-link">Performance Metrics</a>
            <a href="debug.php" class="nav-link">Debug Info</a>
            <a href="correlation.php" class="nav-link">🔍 Correlation</a>
            <a href="../../nagios/" class="nav-link">Back to Nagios</a>
        </div>
        
        <div class="summary">
            <div class="summary-grid">
                <div class="summary-card">
                    <h3 class="<?php echo !empty($results) ? getStatusClass($success_rate >= 80) : ''; ?>"><?php echo !empty($results) ? $passed_tests : '-'; ?>/<?php echo $total_tests; ?></h3>
                    <p>Tests Passed</p>
                </div>
                <div class="summary-card">
                    <h3 class="<?php echo !empty($results) ? getStatusClass($success_rate >= 80) : ''; ?>"><?php echo !empty($results) ? round($success_rate, 1) : '-'; ?>%</h3>
                    <p>Success Rate</p>
                </div>
                <div class="summary-card">
                    <h3><?php echo !empty($results) ? formatTime($total_time) : '-'; ?></h3>
                    <p>Total Test Time</p>
                </div>
                <div class="summary-card">
                    <h3><?php echo $system_info['current_time']; ?></h3>
                    <p>Last Updated</p>
                </div>
            </div>
            
            <div class="system-info">
                <strong>System Information:</strong><br>
                PHP Version: <?php echo $system_info['php_version']; ?> | 
                Server: <?php echo $system_info['server_software']; ?> | 
                file_get_contents: <?php echo $system_info['file_get_contents_available'] ? '✅' : '❌'; ?> | 
                JSON: <?php echo $system_info['json_decode_available'] ? '✅' : '❌'; ?> | 
                cURL: <?php echo $system_info['curl_available'] ? '✅' : '❌'; ?>
            </div>
        </div>
        
        <div class="tests-section">
            <?php if (empty($results)): ?>
            <div class="welcome-message">
                <h3>Ready to Test API Endpoints</h3>
                <p>Choose individual tests below or run all tests at once.</p>
                <p>Large responses are automatically truncated to prevent browser issues.</p>
                <div class="data-warning">
                    ⚠️ Response size limited to <?php echo number_format($MAX_RESPONSE_SIZE); ?> bytes to prevent crashes
                </div>
                
                <div class="test-buttons">
                    <?php foreach ($tests as $key => $test): ?>
                    <a href="?test=<?php echo $key; ?>" class="test-button">🧪 <?php echo $test['name']; ?></a>
                    <?php endforeach; ?>
                </div>
                
                <a href="?run_tests=1" class="run-button">🚀 Run All Tests</a>
            </div>
            <?php else: ?>
            <div style="display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap;">
                <a href="?run_tests=1" class="run-button">🔄 Run All Tests</a>
                <button class="refresh-button" onclick="location.reload()">🔄 Refresh Page</button>
                <a href="index.php" class="refresh-button" style="text-decoration: none; text-align: center;">🏠 Clear Results</a>
            </div>
            <?php endif; ?>
            
            <?php if (!empty($results)): ?>
            <div class="test-grid">
                <?php foreach ($results as $key => $result): ?>
                <div class="test-card">
                    <div class="test-header">
                        <div class="test-title"><?php echo $result['test_name']; ?></div>
                        <div class="test-status <?php echo getStatusClass($result['success'], $result['http_code']); ?>">
                            <?php echo getStatusIcon($result['success'], $result['http_code']); ?>
                        </div>
                    </div>
                    <div class="test-body">
                        <p><em><?php echo $result['test_description']; ?></em></p>
                        
                        <div class="test-details">
                            <div class="detail-item">
                                <div class="detail-label">URL:</div>
                                <div><?php echo htmlspecialchars($result['test_url']); ?></div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Status:</div>
                                <div class="<?php echo getStatusClass($result['success'], $result['http_code']); ?>">
                                    <?php echo $result['success'] ? 'HTTP ' . $result['http_code'] : 'Failed'; ?>
                                </div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Response Time:</div>
                                <div><?php echo formatTime($result['test_time']); ?></div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Data Size:</div>
                                <div><?php echo $result['success'] ? strlen($result['data']) . ' bytes' : 'N/A'; ?></div>
                            </div>
                        </div>
                        
                        <?php if (!$result['success']): ?>
                        <div class="test-response">
                            <strong>Error:</strong> <?php echo htmlspecialchars($result['error']); ?>
                        </div>
                        <?php elseif (isset($result['parsed_data'])): ?>
                        <div class="test-response">
                            <strong>Response Data:</strong>
                            <?php echo htmlspecialchars($result['data']); ?>
                        </div>
                        <?php else: ?>
                        <div class="test-response">
                            <strong>Raw Response:</strong>
                            <?php echo htmlspecialchars($result['data']); ?>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </div>
        
        <div class="footer">
            <p>NagProm API Dashboard | Generated at <?php echo $system_info['current_time']; ?></p>
            <p>This dashboard provides comprehensive monitoring of all NagProm API endpoints.</p>
        </div>
    </div>
    
    <script>
        // Add click handlers for expanding/collapsing responses
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.test-response').forEach(function(element) {
                element.addEventListener('click', function() {
                    this.style.maxHeight = this.style.maxHeight === 'none' ? '300px' : 'none';
                });
            });
        });
    </script>
</body>
</html>
