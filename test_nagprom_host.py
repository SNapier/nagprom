#!/usr/bin/env python3
"""
Test script for nagprom-host.py plugin
Tests various host states and verifies output
"""

import subprocess
import sys
import os
import tempfile
import shutil

def test_nagprom_host_plugin():
    """Test the nagprom-host plugin with various host states"""
    
    # Create temporary directory for test output
    test_dir = tempfile.mkdtemp()
    
    try:
        # Test cases: (hostname, state, state_id, expected_state_name)
        test_cases = [
            ("web-server-01", "UP", "0", "UP"),
            ("db-server-02", "DOWN", "1", "DOWN"), 
            ("app-server-03", "UNREACHABLE", "2", "UNREACHABLE"),
            ("test-host", "UP", "0", "UP"),
            ("down-host", "DOWN", "1", "DOWN")
        ]
        
        print("Testing nagprom-host.py plugin...")
        print("=" * 50)
        
        for hostname, state, state_id, expected_state in test_cases:
            print(f"\nTesting: {hostname} - State: {state} (ID: {state_id})")
            
            # Run the plugin
            cmd = [
                sys.executable, "nagprom-host.py",
                "-H", hostname,
                "-e", state,
                "-i", state_id,
                "-o", test_dir
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"  ✓ Plugin executed successfully")
                print(f"  ✓ Output: {result.stdout.strip()}")
                
                # Check if the .prom file was created
                expected_file = os.path.join(test_dir, f"{hostname.replace(' ', '_').replace('-', '_')}_host_state.prom")
                if os.path.exists(expected_file):
                    print(f"  ✓ Prometheus file created: {os.path.basename(expected_file)}")
                    
                    # Read and display the file content
                    with open(expected_file, 'r') as f:
                        content = f.read()
                        print(f"  ✓ File content preview:")
                        for line in content.split('\n')[:5]:  # Show first 5 lines
                            if line.strip():
                                print(f"    {line}")
                else:
                    print(f"  ✗ Expected file not found: {expected_file}")
                    
            except subprocess.CalledProcessError as e:
                print(f"  ✗ Plugin execution failed: {e}")
                print(f"  ✗ Error output: {e.stderr}")
                
        print("\n" + "=" * 50)
        print("Host state plugin testing completed!")
        
        # List all generated files
        print(f"\nGenerated files in {test_dir}:")
        for file in os.listdir(test_dir):
            if file.endswith('.prom'):
                print(f"  - {file}")
                
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False
        
    finally:
        # Clean up test directory
        shutil.rmtree(test_dir)
        
    return True

if __name__ == "__main__":
    success = test_nagprom_host_plugin()
    sys.exit(0 if success else 1) 