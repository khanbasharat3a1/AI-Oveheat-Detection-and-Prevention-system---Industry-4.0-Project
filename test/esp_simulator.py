#!/usr/bin/env python3
"""
ESP/Arduino Data Simulator
Sends fake sensor data to the motor monitoring system
"""

import time
import random
import requests
import json
import logging
from datetime import datetime
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ESPSimulator:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.endpoint = f"{server_url}/send-data"
        
        # Target optimal values with some realistic variation
        self.base_values = {
            'voltage': 24.0,      # 24V ±2V
            'current': 6.25,      # 6.25A ±1.5A
            'rpm': 2650,          # 2650 RPM ±150
            'temp_c': 26.0,       # 26°C ±8°C
            'humidity': 45.0,     # 45% ±15%
        }
        
        logger.info(f"ESP Simulator initialized for {self.endpoint}")
    
    def generate_sensor_data(self) -> Dict[str, str]:
        """Generate realistic sensor data with random variations"""
        
        # Add realistic variations
        voltage = self.base_values['voltage'] + random.uniform(-2.0, 2.0)
        current = max(0, self.base_values['current'] + random.uniform(-1.5, 1.5))
        rpm = max(0, self.base_values['rpm'] + random.uniform(-150, 150))
        temp_c = self.base_values['temp_c'] + random.uniform(-8.0, 8.0)
        humidity = max(0, min(100, self.base_values['humidity'] + random.uniform(-15.0, 15.0)))
        
        # Convert temperature to Fahrenheit
        temp_f = (temp_c * 9/5) + 32
        
        # Calculate heat index (simplified approximation)
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
    
    def send_data(self, data: Dict[str, str]) -> bool:
        """Send data to the monitoring system"""
        try:
            response = requests.post(
                self.endpoint,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Data sent: V={data['VAL2']}V, I={data['VAL1']}A, RPM={data['VAL3']}")
                return True
            else:
                logger.error(f"❌ Server error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def run_simulation(self, interval: int = 5, duration: int = 300):
        """Run continuous simulation
        
        Args:
            interval: Time between data sends (seconds)
            duration: Total simulation time (seconds, 0 for infinite)
        """
        logger.info(f"🚀 Starting ESP simulation (interval={interval}s)")
        logger.info("📊 Target values: 24V, 6.25A, 2650 RPM, 26°C, 45% humidity")
        
        start_time = time.time()
        count = 0
        
        try:
            while True:
                # Generate and send data
                sensor_data = self.generate_sensor_data()
                success = self.send_data(sensor_data)
                
                count += 1
                elapsed = time.time() - start_time
                
                if success:
                    logger.info(f"📈 Packet {count} sent successfully (elapsed: {elapsed:.1f}s)")
                
                # Check if duration exceeded
                if duration > 0 and elapsed >= duration:
                    logger.info(f"⏰ Simulation completed ({duration}s)")
                    break
                
                # Wait for next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Simulation stopped by user")
        except Exception as e:
            logger.error(f"💥 Simulation error: {e}")

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ESP Data Simulator')
    parser.add_argument('--server', default='http://localhost:5000', 
                       help='Server URL (default: http://localhost:5000)')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Data send interval in seconds (default: 5)')
    parser.add_argument('--duration', type=int, default=0, 
                       help='Simulation duration in seconds (0 for infinite, default: 0)')
    
    args = parser.parse_args()
    
    simulator = ESPSimulator(args.server)
    simulator.run_simulation(args.interval, args.duration)

if __name__ == "__main__":
    main()
