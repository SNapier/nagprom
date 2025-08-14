#!/usr/bin/env python3
"""
Test script for nagprom-service plugin
Demonstrates the enhanced functionality with sample Nagios performance data
"""

import subprocess
import sys
import os

def test_nagprom_plugin():
    """Test the nagprom-service plugin with sample data"""
    
    # Sample test cases with different types of performance data
    test_cases = [
        {
            "name": "HTTP Response Time",
            "host": "webserver01",
            "service": "HTTP",
            "state": "OK",
            "state_id": "0",
            "perfdata": "time=0.123s;1.000;2.000;0.000;10.000"
        },
        {
            "name": "Disk Usage",
            "host": "fileserver01", 
            "service": "Disk Space",
            "state": "WARNING",
            "state_id": "1",
            "perfdata": "disk_usage=85%;80;90;0;100"
        },
        {
            "name": "CPU Load",
            "host": "appserver01",
            "service": "CPU Load",
            "state": "OK", 
            "state_id": "0",
            "perfdata": "load1=0.5;2.0;5.0;0;0 load5=0.8;2.0;5.0;0;0 load15=1.2;2.0;5.0;0;0"
        },
        {
            "name": "Memory Usage",
            "host": "dbserver01",
            "service": "Memory",
            "state": "CRITICAL",
            "state_id": "2", 
            "perfdata": "memory_used=2048MB;1024;2048;0;4096 memory_free=512MB;1024;512;0;4096"
        }
    ]
    
    print("Testing nagprom-service plugin with sample data...")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print(f"Host: {test_case['host']}")
        print(f"Service: {test_case['service']}")
        print(f"State: {test_case['state']} (ID: {test_case['state_id']})")
        print(f"Performance Data: {test_case['perfdata']}")
        
        try:
            # Run the plugin with test data
            cmd = [
                "python3", "nagprom-service.py",
                "-H", test_case["host"],
                "-s", test_case["service"], 
                "-e", test_case["state"],
                "-i", test_case["state_id"],
                "-p", test_case["perfdata"],
                "-o", "./test_output"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Plugin executed successfully")
                print(f"Output: {result.stdout.strip()}")
                
                # Check if output file was created
                output_file = f"./test_output/{test_case['host']}_{test_case['service'].lower().replace(' ', '_')}.prom"
                if os.path.exists(output_file):
                    print(f"✓ Metrics file created: {output_file}")
                    
                    # Show first few lines of the generated file
                    with open(output_file, 'r') as f:
                        lines = f.readlines()
                        print("Generated metrics preview:")
                        for line in lines[:10]:  # Show first 10 lines
                            print(f"  {line.rstrip()}")
                        if len(lines) > 10:
                            print(f"  ... and {len(lines) - 10} more lines")
                else:
                    print(f"✗ Expected output file not found: {output_file}")
            else:
                print(f"✗ Plugin execution failed")
                print(f"Error: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    
    # Cleanup test output directory
    if os.path.exists("./test_output"):
        import shutil
        shutil.rmtree("./test_output")
        print("Cleaned up test output directory")

if __name__ == "__main__":
    # Check if the plugin file exists
    if not os.path.exists("nagprom-service.py"):
        print("Error: nagprom-service.py not found in current directory")
        sys.exit(1)
    
    test_nagprom_plugin() 