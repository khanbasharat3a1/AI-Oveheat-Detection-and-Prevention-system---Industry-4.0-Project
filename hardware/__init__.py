"""
Hardware Communication Package
Handles all hardware interfaces including ESP and PLC
"""

from .esp_handler import ESPHandler
from .plc_manager import PLCManager

__all__ = ['ESPHandler', 'PLCManager']
