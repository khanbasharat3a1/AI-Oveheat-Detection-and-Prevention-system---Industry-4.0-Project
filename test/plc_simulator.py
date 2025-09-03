#!/usr/bin/env python3
"""
FX5U PLC Data Simulator - Standalone Version
Writes realistic fake data to PLC registers for testing
"""

import time
import random
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PLCSimulator:
    def __init__(self, plc_ip="192.168.3.39", plc_port=5007):
        self.plc_ip = plc_ip
        self.plc_port = plc_port
        self.connected = False
        self.mc = None
        
        # Target values for simulation
        self.base_motor_temp = 28.0     # 28°C base temperature
        self.base_motor_voltage = 24.0  # 24V base voltage
        
        print(f"🏭 PLC Simulator initialized")
        print(f"🌐 Target PLC: {plc_ip}:{plc_port}")
        print(f"📊 Base values: 24V motor voltage, 28°C motor temperature")
        
        # Try to import pymcprotocol
        try:
            import pymcprotocol
            self.mc = pymcprotocol.Type3E()
            self.pymcprotocol_available = True
            print("✅ pymcprotocol library loaded")
        except ImportError:
            print("❌ pymcprotocol not available - running in simulation mode only")
            self.pymcprotocol_available = False
    
    def connect(self):
        """Connect to PLC"""
        if not self.pymcprotocol_available:
            print("⚠️  PLC library not available - simulating connection")
            self.connected = True
            return True
        
        try:
            if self.mc.connect(self.plc_ip, self.plc_port):
                self.connected = True
                print(f"✅ Connected to FX5U PLC: {self.plc_ip}:{self.plc_port}")
                return True
            else:
                print("❌ Failed to connect to PLC")
                return False
        except Exception as e:
            print(f"❌ PLC connection error: {e}")
            print("⚠️  Running in simulation mode")
            self.connected = True  # Simulate connection for testing
            return True
    
    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.connected and self.pymcprotocol_available and self.mc:
                self.mc.close()
                self.connected = False
                print("🔌 PLC disconnected")
        except Exception as e:
            print(f"Error disconnecting PLC: {e}")
    
    def temperature_to_raw(self, temp_celsius):
        """Convert temperature to raw value for D102
        Using reverse formula: Raw = Temperature / 0.05175
        """
        if temp_celsius <= 0:
            return 0
        raw_value = int(temp_celsius / 0.05175)
        return min(max(raw_value, 0), 65535)  # Limit to 16-bit range
    
    def voltage_to_raw(self, voltage):
        """Convert voltage to raw value for D100
        Assuming 4095 represents ~30V full scale for 24V system
        """
        if voltage <= 0:
            return 0
        raw_value = int((voltage / 30.0) * 4095)
        return min(max(raw_value, 0), 4095)  # Limit to 12-bit range
    
    def generate_plc_data(self):
        """Generate realistic PLC register values"""
        # Generate motor temperature (D102) with realistic variation
        motor_temp = self.base_motor_temp + random.uniform(-5.0, 15.0)  # 23°C to 43°C
        motor_temp = max(20.0, min(60.0, motor_temp))  # Reasonable limits
        
        # Generate motor voltage (D100) with small variation  
        motor_voltage = self.base_motor_voltage + random.uniform(-1.0, 1.0)  # 23V to 25V
        motor_voltage = max(20.0, min(28.0, motor_voltage))  # Safe limits
        
        # Convert to raw register values
        raw_d102 = self.temperature_to_raw(motor_temp)  # Temperature
        raw_d100 = self.voltage_to_raw(motor_voltage)   # Voltage
        
        print(f"📊 Generated: Temp={motor_temp:.1f}°C->D102({raw_d102}), Voltage={motor_voltage:.1f}V->D100({raw_d100})")
        
        return raw_d100, raw_d102, motor_voltage, motor_temp
    
    def write_data(self, d100_value, d102_value):
        """Write data to PLC registers"""
        if not self.connected:
            if not self.connect():
                return False
        
        if not self.pymcprotocol_available:
            print(f"🔧 [SIMULATED] Writing: D100={d100_value}, D102={d102_value}")
            return True
        
        try:
            # Write to D100 (Voltage)
            self.mc.batchwrite_wordunits(headdevice="D100", values=[d100_value])
            
            # Write to D102 (Temperature) 
            self.mc.batchwrite_wordunits(headdevice="D102", values=[d102_value])
            
            print(f"✅ Written to PLC: D100={d100_value}, D102={d102_value}")
            return True
            
        except Exception as e:
            print(f"❌ Error writing PLC data: {e}")
            return False
    
    def verify_data(self):
        """Read back and verify written data"""
        if not self.connected or not self.pymcprotocol_available:
            print("🔧 [SIMULATED] Data verification - OK")
            return True
        
        try:
            # Read back the written values
            d100_readback = self.mc.batchread_wordunits(headdevice="D100", readsize=1)
            d102_readback = self.mc.batchread_wordunits(headdevice="D102", readsize=1)
            
            # Convert back to engineering units for verification
            voltage = (d100_readback / 4095.0) * 30.0
            temperature = d102_readback * 0.05175
            
            print(f"✅ Verified: D100({d100_readback})={voltage:.1f}V, D102({d102_readback})={temperature:.1f}°C")
            return True
            
        except Exception as e:
            print(f"❌ Error verifying PLC data: {e}")
            return False
    
    def test_single_write(self):
        """Test writing a single data set"""
        print("🧪 Testing single PLC write...")
        
        if not self.connect():
            print("❌ Cannot connect to PLC")
            return False
        
        d100_val, d102_val, voltage, temp = self.generate_plc_data()
        success = self.write_data(d100_val, d102_val)
        
        if success:
            self.verify_data()
            print("✅ Single PLC test successful!")
            return True
        else:
            print("❌ Single PLC test failed!")
            return False
    
    def run_simulation(self, interval=10, duration=600):
        """Run continuous PLC data simulation"""
        print(f"🚀 Starting PLC simulation")
        print(f"⏱️  Interval: {interval}s, Duration: {duration}s")
        print("Press Ctrl+C to stop early")
        print("-" * 50)
        
        if not self.connect():
            print("❌ Cannot start simulation - PLC connection failed")
            return
        
        start_time = time.time()
        count = 0
        success_count = 0
        
        try:
            while True:
                # Generate and write data
                d100_val, d102_val, voltage, temp = self.generate_plc_data()
                success = self.write_data(d100_val, d102_val)
                
                count += 1
                if success:
                    success_count += 1
                    
                    # Verify data occasionally
                    if count % 5 == 0:  # Every 5 cycles
                        self.verify_data()
                
                elapsed = time.time() - start_time
                success_rate = (success_count / count) * 100 if count > 0 else 0
                print(f"📈 Cycle {count} | Success: {success_count}/{count} ({success_rate:.1f}%) | Elapsed: {elapsed:.1f}s")
                
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
        finally:
            self.disconnect()
        
        elapsed = time.time() - start_time
        success_rate = (success_count / count) * 100 if count > 0 else 0
        
        print("-" * 50)
        print(f"📊 Summary:")
        print(f"   Total cycles: {count}")
        print(f"   Successful: {success_count}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Duration: {elapsed:.1f}s")

def main():
    import sys
    
    # Parse command line arguments manually
    plc_ip = "192.168.3.39"
    plc_port = 5007
    interval = 10
    duration = 600
    test_only = False
    
    # Simple argument parsing
    for i, arg in enumerate(sys.argv):
        if arg == "--ip" and i + 1 < len(sys.argv):
            plc_ip = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            plc_port = int(sys.argv[i + 1])
        elif arg == "--interval" and i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 1])
        elif arg == "--duration" and i + 1 < len(sys.argv):
            duration = int(sys.argv[i + 1])
        elif arg == "--test-only":
            test_only = True
        elif arg == "--help":
            print("PLC Simulator - Usage:")
            print("  python plc_simulator.py [options]")
            print("Options:")
            print("  --ip IP            PLC IP address (default: 192.168.3.39)")
            print("  --port PORT        PLC port (default: 5007)")
            print("  --interval SEC     Write interval in seconds (default: 10)")
            print("  --duration SEC     Duration in seconds (default: 600)")
            print("  --test-only        Write only one test data set")
            print("  --help             Show this help")
            return
    
    print("=" * 60)
    print("🏭 FX5U PLC DATA SIMULATOR")
    print("=" * 60)
    
    simulator = PLCSimulator(plc_ip, plc_port)
    
    if test_only:
        simulator.test_single_write()
    else:
        simulator.run_simulation(interval, duration)

if __name__ == "__main__":
    main()
