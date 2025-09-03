"""
System Configuration
All settings and thresholds for the motor monitoring system
"""

import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """System configuration class"""
    
    # PLC Configuration
    PLC_IP: str = os.getenv('PLC_IP', '192.168.3.39')
    PLC_PORT: int = int(os.getenv('PLC_PORT', 5007))
    
    # Flask Configuration
    FLASK_HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT: int = int(os.getenv('FLASK_PORT', 5000))
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///data/motor_monitoring.db')
    CSV_EXPORT_PATH: str = 'data/sensor_data.csv'
    
    # Connection Timeouts (seconds)
    ESP_TIMEOUT: int = 30
    PLC_TIMEOUT: int = 60
    DATA_CLEANUP_INTERVAL: int = 10
    
    # OPTIMAL VALUES - 24V Motor System
    OPTIMAL_MOTOR_TEMP: float = 40.0       # Motor temp < 40°C
    OPTIMAL_VOLTAGE: float = 24.0          # 24V DC motor
    OPTIMAL_CURRENT: float = 6.25          # 6.25A current
    OPTIMAL_DHT_TEMP: float = 24.0         # Ambient temp 24°C
    OPTIMAL_DHT_HUMIDITY: float = 40.0     # Humidity 40%
    OPTIMAL_RPM: float = 2750.0            # RPM 2750
    
    # HEALTH THRESHOLDS
    # Motor Temperature
    MOTOR_TEMP_EXCELLENT: float = 35.0
    MOTOR_TEMP_GOOD: float = 40.0
    MOTOR_TEMP_WARNING: float = 50.0
    MOTOR_TEMP_CRITICAL: float = 60.0
    
    # Voltage (24V ±15%)
    VOLTAGE_MIN_CRITICAL: float = 20.0
    VOLTAGE_MIN_WARNING: float = 22.0
    VOLTAGE_MAX_WARNING: float = 26.0
    VOLTAGE_MAX_CRITICAL: float = 28.0
    
    # Current (6.25A ±30%)
    CURRENT_MIN_WARNING: float = 4.0
    CURRENT_OPTIMAL_MIN: float = 5.0
    CURRENT_OPTIMAL_MAX: float = 7.5
    CURRENT_MAX_WARNING: float = 9.0
    CURRENT_MAX_CRITICAL: float = 12.0
    
    # RPM (2750 ±8%)
    RPM_MIN_CRITICAL: float = 2400.0
    RPM_MIN_WARNING: float = 2600.0
    RPM_MAX_WARNING: float = 2900.0
    RPM_MAX_CRITICAL: float = 3100.0
    
    # Environmental
    DHT_TEMP_MAX_WARNING: float = 30.0
    DHT_TEMP_MAX_CRITICAL: float = 35.0
    DHT_HUMIDITY_MIN_WARNING: float = 30.0
    DHT_HUMIDITY_MAX_WARNING: float = 70.0
    DHT_HUMIDITY_MAX_CRITICAL: float = 80.0

def setup_logging():
    """Setup application logging"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/application.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# Global config instance
config = Config()
