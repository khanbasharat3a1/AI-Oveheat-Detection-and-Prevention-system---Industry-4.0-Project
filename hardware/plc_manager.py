"""
FX5U PLC Manager
Handles communication with Mitsubishi FX5U PLC
"""

import logging
import pymcprotocol
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PLCManager:
    def __init__(self, config):
        self.config = config
        self.mc = pymcprotocol.Type3E()
        self.connected = False
        self.last_data = {}
        logger.info(f"PLC Manager initialized for {config.PLC_IP}:{config.PLC_PORT}")
    
    def connect(self) -> bool:
        """Connect to FX5U PLC"""
        try:
            if self.mc.connect(self.config.PLC_IP, self.config.PLC_PORT):
                self.connected = True
                logger.info(f"FX5U PLC connected: {self.config.PLC_IP}:{self.config.PLC_PORT}")
                return True
            else:
                self.connected = False
                logger.error("Failed to connect to FX5U PLC")
                return False
        except Exception as e:
            self.connected = False
            logger.error(f"PLC connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from FX5U PLC"""
        try:
            if self.connected:
                self.mc.close()
                self.connected = False
                logger.info("FX5U PLC disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting PLC: {e}")
    
    def convert_voltage(self, raw_value: int) -> float:
        """Convert D100 raw value to voltage (24V system)
        
        Args:
            raw_value: Raw ADC value from D100 register
            
        Returns:
            Voltage in volts
        """
        if raw_value <= 0:
            return 0.0
        
        # Scale for 24V system (assuming 4095 = ~30V max range)
        voltage = (raw_value / 4095.0) * 30.0
        return round(voltage, 1)
    
    def convert_temperature(self, raw_value: int) -> float:
        """Convert D102 raw value to temperature using formula:
        Temperature (°C) = 0.05175 × Raw Value
        
        Args:
            raw_value: Raw ADC value from D102 register
            
        Returns:
            Temperature in Celsius
        """
        if raw_value <= 0:
            return 0.0
        
        temperature = 0.05175 * raw_value
        return round(temperature, 1)
    
    def read_data(self) -> Dict[str, any]:
        """Read data from FX5U PLC registers"""
        if not self.connected:
            if not self.connect():
                return {'plc_connected': False}
        
        try:
            # Read raw values from FX5U registers
            raw_d100 = self.mc.batchread_wordunits(headdevice="D100", readsize=1)  # Voltage
            raw_d102 = self.mc.batchread_wordunits(headdevice="D102", readsize=1)  # Temperature
            
            # Convert to engineering units
            motor_voltage = self.convert_voltage(raw_d100)
            motor_temp = self.convert_temperature(raw_d102)
            
            self.last_data = {
                'plc_motor_temp': motor_temp,
                'plc_motor_voltage': motor_voltage,
                'plc_connected': True,
                'raw_d100': raw_d100,
                'raw_d102': raw_d102
            }
            
            logger.debug(f"PLC readings: D100({raw_d100}) -> {motor_voltage}V, "
                        f"D102({raw_d102}) -> {motor_temp}°C")
            
            return self.last_data
            
        except Exception as e:
            logger.error(f"Error reading PLC data: {e}")
            self.connected = False
            return {'plc_connected': False}
    
    def get_connection_status(self) -> Dict[str, any]:
        """Get PLC connection status"""
        return {
            'connected': self.connected,
            'ip': self.config.PLC_IP,
            'port': self.config.PLC_PORT,
            'last_data': self.last_data
        }
    
    def test_connection(self) -> bool:
        """Test PLC connection"""
        try:
            test_data = self.read_data()
            return test_data.get('plc_connected', False)
        except Exception as e:
            logger.error(f"PLC connection test failed: {e}")
            return False
