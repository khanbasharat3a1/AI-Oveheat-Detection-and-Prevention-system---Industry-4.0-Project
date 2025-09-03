#!/usr/bin/env python3
"""
ESP/Arduino Data Simulator - Standalone Version
Sends realistic fake sensor data to the motor monitoring system
"""

import time
import random
import requests
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ESPSimulator:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.endpoint = f"{server_url}/send-data"
        
        # Target optimal values with realistic variation
        self.base_values = {
            'voltage': 24.0,      # 24V ±2V
            'current': 6.25,      # 6.25A ±1.5A
            'rpm': 2650,          # 2650 RPM ±150
            'temp_c': 26.0,       # 26°C ±8°C
            'humidity': 45.0,     # 45% ±15%
        }
        
        print(f"🔌 ESP Simulator initialized")
        print(f"🌐 Target server: {self.endpoint}")
        print(f"📊 Base values: 24V, 6.25A, 2650 RPM, 26°C, 45%RH")
    
    def generate_sensor_data(self):
        """Generate realistic sensor data with random variations"""
        
        # Add realistic variations
        voltage = self.base_values['voltage'] + random.uniform(-2.0, 2.0)
        current = max(0, self.base_values['current'] + random.uniform(-1.5, 1.5))
        rpm = max(0, self.base_values['rpm'] + random.uniform(-150, 150))
        temp_c = self.base_values['temp_c'] + random.uniform(-8.0, 8.0)
        humidity = max(0, min(100, self.base_values['humidity'] + random.uniform(-15.0, 15.0)))
        
        # Convert temperature to Fahrenheit
        temp_f = (temp_c * 9/5) + 32
        
        # Calculate heat index (simplified)
        heat_index_c = temp_c + (0.01 * humidity * (temp_c - 14.55))
        heat_index_f = (heat_index_c * 9/5) + 32
        
        # Generate relay statuses (mostly OFF with occasional ON)
        relay1 = "ON" if current > 8.0 else "OFF"  # Current protection
        relay2 = "ON" if voltage < 22.0 or voltage > 26.0 else "OFF"  # Voltage protection
        relay3 = "ON" if temp_c > 35.0 else "OFF"  # Temperature protection
        
        # Combined status
        if relay1 == "ON" or relay2 == "ON" or relay3 == "ON":
            combined = "BUZ"  # Alarm state
        else:
            combined = "NOR"  # Normal state
        
        # Format data as expected by the system
        data = {
            "TYPE": "ADU_TEXT",
            "VAL1": f"{current:.2f}",        # Current in Amperes
            "VAL2": f"{voltage:.2f}",        # Voltage in Volts
            "VAL3": f"{int(rpm)}",           # RPM
            "VAL4": f"{temp_c:.1f}",         # Temperature Celsius
            "VAL5": f"{humidity:.1f}",       # Humidity %
            "VAL6": f"{temp_f:.1f}",         # Temperature Fahrenheit
            "VAL7": f"{heat_index_c:.1f}",   # Heat Index Celsius
            "VAL8": f"{heat_index_f:.1f}",   # Heat Index Fahrenheit
            "VAL9": relay1,                  # Relay 1 Status
            "VAL10": relay2,                 # Relay 2 Status
            "VAL11": relay3,                 # Relay 3 Status
            "VAL12": combined                # Combined Status
        }
        
        return data
    
    def send_data(self, data):
        """Send data to the monitoring system"""
        try:
            response = requests.post(
                self.endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Data sent: V={data['VAL2']}V, I={data['VAL1']}A, RPM={data['VAL3']}, T={data['VAL4']}°C")
                return True
            else:
                print(f"❌ Server error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error: Cannot reach {self.server_url}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ Timeout: Server not responding")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_single_send(self):
        """Test sending a single data packet"""
        print("🧪 Testing single data send...")
        sensor_data = self.generate_sensor_data()
        success = self.send_data(sensor_data)
        
        if success:
            print("✅ Single test successful!")
            return True
        else:
            print("❌ Single test failed!")
            return False
    
    def run_simulation(self, interval=5, duration=300):
        """Run continuous simulation"""
        print(f"🚀 Starting ESP simulation")
        print(f"⏱️  Interval: {interval}s, Duration: {duration}s")
        print("Press Ctrl+C to stop early")
        print("-" * 50)
        
        start_time = time.time()
        count = 0
        success_count = 0
        
        try:
            while True:
                # Generate and send data
                sensor_data = self.generate_sensor_data()
                success = self.send_data(sensor_data)
                
                count += 1
                if success:
                    success_count += 1
                
                elapsed = time.time() - start_time
                print(f"📈 Packet {count} | Success: {success_count}/{count} | Elapsed: {elapsed:.1f}s")
                
                # Check if duration exceeded
                if duration > 0 and elapsed >= duration:
                    print(f"⏰ Simulation completed ({duration}s)")
                    break
                
                # Wait for next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
        except Exception as e:
            print(f"💥 Simulation error: {e}")
        
        elapsed = time.time() - start_time
        success_rate = (success_count / count) * 100 if count > 0 else 0
        
        print("-" * 50)
        print(f"📊 Summary:")
        print(f"   Total packets: {count}")
        print(f"   Successful: {success_count}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Duration: {elapsed:.1f}s")

def main():
    import sys
    
    # Parse command line arguments manually (no argparse dependency)
    server_url = "http://localhost:5000"
    interval = 5
    duration = 300
    test_only = False
    
    # Simple argument parsing
    for i, arg in enumerate(sys.argv):
        if arg == "--server" and i + 1 < len(sys.argv):
            server_url = sys.argv[i + 1]
        elif arg == "--interval" and i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 1])
        elif arg == "--duration" and i + 1 < len(sys.argv):
            duration = int(sys.argv[i + 1])
        elif arg == "--test-only":
            test_only = True
        elif arg == "--help":
            print("ESP Simulator - Usage:")
            print("  python esp_simulator.py [options]")
            print("Options:")
            print("  --server URL       Server URL (default: http://localhost:5000)")
            print("  --interval SEC     Send interval in seconds (default: 5)")
            print("  --duration SEC     Duration in seconds (default: 300)")
            print("  --test-only        Send only one test packet")
            print("  --help             Show this help")
            return
    
    print("=" * 60)
    print("🔌 ESP/ARDUINO DATA SIMULATOR")
    print("=" * 60)
    
    simulator = ESPSimulator(server_url)
    
    if test_only:
        simulator.test_single_send()
    else:
        simulator.run_simulation(interval, duration)

if __name__ == "__main__":
    main()
