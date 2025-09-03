"""
ESP/Arduino Data Handler
Processes incoming data from ESP module
"""

import logging
from datetime import datetime
from typing import Dict, Any
from flask import request, jsonify
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

class ESPHandler:
    def __init__(self, config, db_manager, health_analyzer, socketio: SocketIO):
        self.config = config
        self.db_manager = db_manager
        self.health_analyzer = health_analyzer
        self.socketio = socketio
        logger.info("ESP Handler initialized")
    
    def process_esp_data(self, app_instance, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming ESP data"""
        try:
            if not data:
                return {'status': 'error', 'message': 'No data received'}
            
            current_time = datetime.now()
            
            # Parse ESP data with validation
            esp_data = {
                'esp_current': self._safe_float(data.get('VAL1')),
                'esp_voltage': self._safe_float(data.get('VAL2')),
                'esp_rpm': self._safe_float(data.get('VAL3')),
                'env_temp_c': self._safe_float(data.get('VAL4')),
                'env_humidity': self._safe_float(data.get('VAL5')),
                'env_temp_f': self._safe_float(data.get('VAL6')),
                'heat_index_c': self._safe_float(data.get('VAL7')),
                'heat_index_f': self._safe_float(data.get('VAL8')),
                'relay1_status': data.get('VAL9', 'OFF'),
                'relay2_status': data.get('VAL10', 'OFF'),
                'relay3_status': data.get('VAL11', 'OFF'),
                'combined_status': data.get('VAL12', 'NOR'),
                'esp_connected': True
            }
            
            # Update app instance data
            app_instance.latest_data.update(esp_data)
            app_instance.system_status['esp_connected'] = True
            app_instance.system_status['esp_last_seen'] = current_time.isoformat()
            app_instance.system_status['last_update'] = current_time.isoformat()
            
            # Save to database
            combined_data = {**app_instance.latest_data}
            self.db_manager.save_sensor_data(combined_data, app_instance.system_status)
            
            # Emit real-time update
            self.socketio.emit('sensor_update', combined_data)
            
            logger.info(f"ESP data processed: Current={esp_data.get('esp_current')}A, "
                       f"Voltage={esp_data.get('esp_voltage')}V, RPM={esp_data.get('esp_rpm')}")
            
            return {'status': 'success', 'message': 'Data processed successfully'}
            
        except Exception as e:
            logger.error(f"Error processing ESP data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        if value is None or value == '' or value == '0':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_esp_status(self, app_instance) -> Dict[str, Any]:
        """Get current ESP connection status"""
        return {
            'connected': app_instance.system_status['esp_connected'],
            'last_seen': app_instance.system_status.get('esp_last_seen'),
            'data_count': len([k for k in app_instance.latest_data.keys() if k.startswith('esp_')])
        }
