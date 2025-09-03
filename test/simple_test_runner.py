#!/usr/bin/env python3
"""
Simple Test Runner - No Subprocess Issues
Runs ESP and PLC tests in separate threads
"""

import time
import threading
import sys
import os

print("=" * 60)
print("🧪 SIMPLE AI MOTOR MONITORING TEST SUITE")
print("=" * 60)

def run_esp_test():
    """Run ESP test in thread"""
    print("🔌 Starting ESP test thread...")
    try:
        # Import and run ESP simulator
        sys.path.append(os.path.dirname(__file__))
        from esp_simulator import ESPSimulator
        
        simulator = ESPSimulator("http://10.133.143.247:5000")
        
        # Test single send first
        if simulator.test_single_send():
            print("🔌 ESP single test passed - starting continuous...")
            simulator.run_simulation(interval=5, duration=60)  # 1 minute
        else:
            print("🔌 ESP single test failed - check if main app is running")
            
    except ImportError as e:
        print(f"🔌 ESP test import error: {e}")
    except Exception as e:
        print(f"🔌 ESP test error: {e}")

def run_plc_test():
    """Run PLC test in thread"""
    print("🏭 Starting PLC test thread...")
    try:
        # Import and run PLC simulator
        sys.path.append(os.path.dirname(__file__))
        from plc_simulator import PLCSimulator
        
        simulator = PLCSimulator("192.168.3.39", 5007)
        
        # Test single write first
        if simulator.test_single_write():
            print("🏭 PLC single test passed - starting continuous...")
            simulator.run_simulation(interval=10, duration=60)  # 1 minute
        else:
            print("🏭 PLC single test completed (may be simulated)")
            
    except ImportError as e:
        print(f"🏭 PLC test import error: {e}")
    except Exception as e:
        print(f"🏭 PLC test error: {e}")

def main():
    print("🚀 Starting both tests...")
    print("⏱️  Each test will run for 60 seconds")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start threads
    esp_thread = threading.Thread(target=run_esp_test, daemon=True)
    plc_thread = threading.Thread(target=run_plc_test, daemon=True)
    
    try:
        esp_thread.start()
        time.sleep(2)  # Brief delay
        plc_thread.start()
        
        # Wait for threads to complete
        esp_thread.join()
        plc_thread.join()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")

if __name__ == "__main__":
    main()
