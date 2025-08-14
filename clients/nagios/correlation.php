<?php
/**
 * NagProm Alert Correlation Dashboard
 * 
 * Alert correlation and pattern analysis dashboard
 * Uses file_get_contents() instead of curl for compatibility
 */

// Configuration
$API_BASE = "http://127.0.0.1/nagprom/api/v1";
$TIMEOUT = 10; // seconds
$MAX_RESPONSE_SIZE = 50000; // 50KB limit

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

// Get query parameters
$time_window = $_GET['time_window'] ?? 900; // 15 minutes default
$service = $_GET['service'] ?? '';
$host = $_GET['host'] ?? '';
$correlation_type = $_GET['type'] ?? '';

// Build API URL with filters
$api_url = $API_BASE . "/sre/alerts/correlation?time_window=" . urlencode($time_window);
if ($service) $api_url .= "&service=" . urlencode($service);
if ($host) $api_url .= "&host=" . urlencode($host);
if ($correlation_type) $api_url .= "&type=" . urlencode($correlation_type);

// Get correlation data
$correlation_response = makeRequest($api_url, $TIMEOUT);
$correlation_data = null;

if ($correlation_response['success']) {
    $correlation_data = json_decode($correlation_response['data'], true);
}

// Get alert metrics
$metrics_response = makeRequest($API_BASE . "/sre/alerts/metrics", $TIMEOUT);
$metrics_data = null;

if ($metrics_response['success']) {
    $metrics_data = json_decode($metrics_response['data'], true);
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NagProm - Alert Correlation Dashboard</title>
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
        
        .nav {
            background: #3a3a3a;
            padding: 15px 20px;
            border-bottom: 1px solid #4a4a4a;
        }
        
        .nav a {
            color: #48bb78;
            text-decoration: none;
            margin-right: 20px;
            padding: 8px 12px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .nav a:hover {
            background-color: #4a4a4a;
        }
        
        .nav a.active {
            background-color: #48bb78;
            color: #1a1a1a;
        }
        
        .content {
            padding: 20px;
        }
        
        .filters {
            background: #3a3a3a;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #4a4a4a;
        }
        
        .filters form {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .filters label {
            font-weight: 500;
            margin-right: 5px;
            color: #e0e0e0;
        }
        
        .filters input, .filters select {
            padding: 8px 12px;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            font-size: 14px;
            background: #2d2d2d;
            color: #e0e0e0;
        }
        
        .filters button {
            background: #48bb78;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .filters button:hover {
            background: #38a169;
        }
        
        .refresh-button {
            background: #48bb78;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 20px;
        }
        
        .refresh-button:hover {
            background: #38a169;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: #3a3a3a;
            border: 1px solid #4a4a4a;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #48bb78;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #b0b0b0;
            font-size: 0.9em;
        }
        
        .correlations {
            margin-top: 20px;
        }
        
        .correlation-card {
            background: #3a3a3a;
            border: 1px solid #4a4a4a;
            border-radius: 6px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        
        .correlation-header {
            background: #4a4a4a;
            padding: 15px;
            border-bottom: 1px solid #4a4a4a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .correlation-type {
            background: #48bb78;
            color: #1a1a1a;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            text-transform: uppercase;
            font-weight: bold;
        }
        
        .correlation-confidence {
            font-weight: bold;
            color: #48bb78;
        }
        
        .correlation-body {
            padding: 15px;
        }
        
        .alert-list {
            margin-top: 10px;
        }
        
        .alert-item {
            background: #2d2d2d;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            border-left: 4px solid #48bb78;
        }
        
        .alert-severity {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .severity-critical { background: #f56565; color: white; }
        .severity-warning { background: #ed8936; color: white; }
        .severity-info { background: #4299e1; color: white; }
        
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        
        .status.success { background: #2d3748; color: #48bb78; border: 1px solid #48bb78; }
        .status.error { background: #2d3748; color: #f56565; border: 1px solid #f56565; }
        .status.warning { background: #2d3748; color: #ed8936; border: 1px solid #ed8936; }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #b0b0b0;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Alert Correlation Dashboard</h1>
            <p>Machine Learning-Powered Alert Pattern Analysis</p>
        </div>
        
        <div class="nav">
            <a href="index.php">📊 Main Dashboard</a>
            <a href="metrics.php">📈 Metrics</a>
            <a href="debug.php">🐛 Debug</a>
            <a href="correlation.php" class="active">🔍 Correlation</a>
        </div>
        
        <div class="content">
            <!-- Status Messages -->
            <?php if (!$correlation_response['success']): ?>
                <div class="status error">
                    ❌ Failed to load correlation data: <?php echo htmlspecialchars($correlation_response['error']); ?>
                </div>
            <?php endif; ?>
            
            <?php if (!$metrics_response['success']): ?>
                <div class="status error">
                    ❌ Failed to load metrics: <?php echo htmlspecialchars($metrics_response['error']); ?>
                </div>
            <?php endif; ?>
            
            <!-- Filters -->
            <div class="filters">
                <form method="GET">
                    <label>Time Window:</label>
                    <select name="time_window">
                        <option value="300" <?php echo $time_window == 300 ? 'selected' : ''; ?>>5 minutes</option>
                        <option value="900" <?php echo $time_window == 900 ? 'selected' : ''; ?>>15 minutes</option>
                        <option value="1800" <?php echo $time_window == 1800 ? 'selected' : ''; ?>>30 minutes</option>
                        <option value="3600" <?php echo $time_window == 3600 ? 'selected' : ''; ?>>1 hour</option>
                        <option value="7200" <?php echo $time_window == 7200 ? 'selected' : ''; ?>>2 hours</option>
                    </select>
                    
                    <label>Service:</label>
                    <input type="text" name="service" value="<?php echo htmlspecialchars($service); ?>" placeholder="Filter by service">
                    
                    <label>Host:</label>
                    <input type="text" name="host" value="<?php echo htmlspecialchars($host); ?>" placeholder="Filter by host">
                    
                    <label>Type:</label>
                    <select name="type">
                        <option value="">All Types</option>
                        <option value="temporal" <?php echo $correlation_type == 'temporal' ? 'selected' : ''; ?>>Temporal</option>
                        <option value="spatial" <?php echo $correlation_type == 'spatial' ? 'selected' : ''; ?>>Spatial</option>
                        <option value="similarity" <?php echo $correlation_type == 'similarity' ? 'selected' : ''; ?>>Similarity</option>
                        <option value="dependency" <?php echo $correlation_type == 'dependency' ? 'selected' : ''; ?>>Dependency</option>
                    </select>
                    
                    <button type="submit">Apply Filters</button>
                </form>
            </div>
            
            <!-- Refresh Button -->
            <button class="refresh-button" onclick="location.reload()">🔄 Refresh Data</button>
            
            <!-- Metrics Overview -->
            <?php if ($metrics_data && $metrics_data['success']): ?>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value"><?php echo number_format($metrics_data['data']['total_alerts'] ?? 0); ?></div>
                        <div class="metric-label">Total Alerts</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value"><?php echo number_format($metrics_data['data']['correlation_rate'] ?? 0, 1); ?>%</div>
                        <div class="metric-label">Correlation Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value"><?php echo number_format($metrics_data['data']['clusters_created'] ?? 0); ?></div>
                        <div class="metric-label">Clusters Created</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value"><?php echo number_format($metrics_data['data']['noise_suppressed'] ?? 0); ?></div>
                        <div class="metric-label">Noise Suppressed</div>
                    </div>
                </div>
            <?php endif; ?>
            
            <!-- Alert Correlations -->
            <div class="correlations">
                <h2>🔍 Alert Correlations</h2>
                
                <?php if ($correlation_data && $correlation_data['success'] && !empty($correlation_data['data']['correlations'])): ?>
                    <?php foreach ($correlation_data['data']['correlations'] as $correlation): ?>
                        <div class="correlation-card">
                            <div class="correlation-header">
                                <div>
                                    <span class="correlation-type"><?php echo htmlspecialchars($correlation['correlation_type']); ?></span>
                                    <span style="margin-left: 10px; font-weight: bold;">
                                        <?php echo $correlation['alert_count']; ?> alerts correlated
                                    </span>
                                </div>
                                <div class="correlation-confidence">
                                    <?php echo number_format($correlation['confidence_score'] * 100, 1); ?>% confidence
                                </div>
                            </div>
                            
                            <div class="correlation-body">
                                <?php if (!empty($correlation['root_cause_candidates'])): ?>
                                    <p><strong>Root Cause Candidates:</strong> <?php echo htmlspecialchars(implode(', ', $correlation['root_cause_candidates'])); ?></p>
                                <?php endif; ?>
                                
                                <?php if (!empty($correlation['impact_assessment'])): ?>
                                    <p><strong>Impact:</strong> <?php echo htmlspecialchars($correlation['impact_assessment']); ?></p>
                                <?php endif; ?>
                                
                                <div class="alert-list">
                                    <h4>Alerts in Cluster:</h4>
                                    <?php foreach ($correlation['alerts'] as $alert): ?>
                                        <div class="alert-item">
                                            <span class="alert-severity severity-<?php echo strtolower($alert['severity']); ?>">
                                                <?php echo strtoupper($alert['severity']); ?>
                                            </span>
                                            <strong><?php echo htmlspecialchars($alert['title']); ?></strong>
                                            <br>
                                            <small>
                                                <?php echo htmlspecialchars($alert['service']); ?> on <?php echo htmlspecialchars($alert['host']); ?> - 
                                                <?php echo date('Y-m-d H:i:s', strtotime($alert['timestamp'])); ?>
                                            </small>
                                        </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <div class="no-data">
                        <h3>No Alert Correlations Found</h3>
                        <p>No alert correlations were detected in the specified time window and filters.</p>
                        <p>This could mean:</p>
                        <ul style="text-align: left; display: inline-block;">
                            <li>No alerts have been received recently</li>
                            <li>Alerts are not similar enough to be correlated</li>
                            <li>The time window is too short</li>
                            <li>Filters are too restrictive</li>
                        </ul>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
