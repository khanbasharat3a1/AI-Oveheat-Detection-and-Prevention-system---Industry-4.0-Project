#!/usr/bin/env python3
"""
FX5U PLC Data Simulator
Writes fake data to PLC registers for testing
"""

import time
import random
import logging
from datetime import datetime
import pymcprotocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PLCSimulator:
    def __init__(self, plc_ip="192.168.3.39", plc_port=5007):
        self.plc_ip = plc_ip
        self.plc_port = plc_port
        self.mc = pymcprotocol.Type3E()
        self.connected = False
        
        # Target values for simulation
        self.base_motor_temp = 28.0     # 28°C base temperature
        self.base_motor_voltage = 24.0  # 24V base voltage
        
        logger.info(f"PLC Simulator initialized for {plc_ip}:{plc_port}")
    
    def connect(self) -> bool:
        """Connect to PLC"""
        try:
            if self.mc.connect(self.plc_ip, self.plc_port):
                self.connected = True
                logger.info(f"✅ Connected to FX5U PLC: {self.plc_ip}:{self.plc_port}")
                return True
            else:
                logger.error("❌ Failed to connect to PLC")
                return False
        except Exception as e:
            logger.error(f"❌ PLC connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.connected:
                self.mc.close()
                self.connected = False
                logger.info("🔌 PLC disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting PLC: {e}")
    
    def temperature_to_raw(self, temp_celsius: float) -> int:
        """Convert temperature to raw value for D102
        Using reverse formula: Raw = Temperature / 0.05175
        """
        if temp_celsius <= 0:
            return 0
        raw_value = int(temp_celsius / 0.05175)
        return min(max(raw_value, 0), 65535)  # Limit to 16-bit range
    
    def voltage_to_raw(self, voltage: float) -> int:
        """Convert voltage to raw value for D100
        Assuming 4095 represents ~30V full scale for 24V system
        """
        if voltage <= 0:
            return 0
        raw_value = int((voltage / 30.0) * 4095)
        return min(max(raw_value, 0), 4095)  # Limit to 12-bit range
    
    def generate_plc_data(self) -> tuple[int, int]:
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
        
        logger.debug(f"Generated: Temp={motor_temp:.1f}°C->raw({raw_d102}), "
                    f"Voltage={motor_voltage:.1f}V->raw({raw_d100})")
        
        return raw_d100, raw_d102
    
    def write_data(self, d100_value: int, d102_value: int) -> bool:
        """Write data to PLC registers"""
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            # Write to D100 (Voltage)
            self.mc.batchwrite_wordunits(headdevice="D100", values=[d100_value])
            
            # Write to D102 (Temperature) 
            self.mc.batchwrite_wordunits(headdevice="D102", values=[d102_value])
            
            logger.info(f"📝 Written: D100={d100_value} (voltage), D102={d102_value} (temp)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing PLC data: {e}")
            self.connected = False
            return False
    
    def verify_data(self) -> bool:
        """Read back and verify written data"""
        if not self.connected:
            return False
        
        try:
            # Read back the written values
            d100_readback = self.mc.batchread_wordunits(headdevice="D100", readsize=1)
            d102_readback = self.mc.batchread_wordunits(headdevice="D102", readsize=1)
            
            # Convert back to engineering units for verification
            voltage = (d100_readback / 4095.0) * 30.0
            temperature = d102_readback * 0.05175
            
            logger.info(f"✅ Verified: D100({d100_readback})={voltage:.1f}V, "
                       f"D102({d102_readback})={temperature:.1f}°C")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying PLC data: {e}")
            return False
    
    def run_simulation(self, interval: int = 10, duration: int = 600):
        """Run continuous PLC data simulation
        
        Args:
            interval: Time between writes (seconds)
            duration: Total simulation time (seconds, 0 for infinite)
        """
        logger.info(f"🚀 Starting PLC simulation (interval={interval}s)")
        logger.info("📊 Target values: ~24V motor voltage, ~28°C motor temperature")
        
        if not self.connect():
            logger.error("Cannot start simulation - PLC connection failed")
            return
        
        start_time = time.time()
        count = 0
        
        try:
            while True:
                # Generate and write data
                d100_val, d102_val = self.generate_plc_data()
                success = self.write_data(d100_val, d102_val)
                
                if success:
                    count += 1
                    elapsed = time.time() - start_time
                    logger.info(f"📈 Cycle {count} completed (elapsed: {elapsed:.1f}s)")
                    
                    # Verify data occasionally
                    if count % 5 == 0:  # Every 5 cycles
                        self.verify_data()
                
                # Check if duration exceeded
                if duration > 0 and (time.time() - start_time) >= duration:
                    logger.info(f"⏰ Simulation completed ({duration}s)")
                    break
                
                # Wait for next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Simulation stopped by user")
        except Exception as e:
            logger.error(f"💥 Simulation error: {e}")
        finally:
            self.disconnect()

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PLC Data Simulator')
    parser.add_argument('--ip', default='192.168.3.39', 
                       help='PLC IP address (default: 192.168.3.39)')
    parser.add_argument('--port', type=int, default=5007,
                       help='PLC port (default: 5007)')
    parser.add_argument('--interval', type=int, default=10, 
                       help='Data write interval in seconds (default: 10)')
    parser.add_argument('--duration', type=int, default=0, 
                       help='Simulation duration in seconds (0 for infinite, default: 0)')
    parser.add_argument('--test-only', action='store_true',
                       help='Only test connection and write one data set')
    
    args = parser.parse_args()
    
    simulator = PLCSimulator(args.ip, args.port)
    
    if args.test_only:
        logger.info("🧪 Running connection test only")
        if simulator.connect():
            d100_val, d102_val = simulator.generate_plc_data()
            simulator.write_data(d100_val, d102_val)
            simulator.verify_data()
            simulator.disconnect()
        else:
            logger.error("Connection test failed")
    else:
        simulator.run_simulation(args.interval, args.duration)

if __name__ == "__main__":
    main()
