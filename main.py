#!/usr/bin/env python3
"""
AI-Enabled Industrial Motor Health & Environment Monitoring System
Main Application Entry Point
Version 4.0 - Modular Architecture
"""

import os
import threading
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from config import Config, setup_logging
from hardware.esp_handler import ESPHandler
from hardware.plc_manager import PLCManager
from ai.health_analyzer import HealthAnalyzer
from database.manager import DatabaseManager
from api.routes import setup_routes, setup_websocket_events

# Setup logging
logger = setup_logging()

class MotorMonitoringSystem:
    def __init__(self):
        self.config = Config()
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'motor_monitoring_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.db_manager = DatabaseManager(self.config)
        self.plc_manager = PLCManager(self.config)
        self.health_analyzer = HealthAnalyzer(self.config)
        self.esp_handler = ESPHandler(self.config, self.db_manager, self.health_analyzer, self.socketio)
        
        # System state
        self.latest_data = {}
        self.system_status = {
            'esp_connected': False,
            'plc_connected': False,
            'ai_model_status': 'Initializing',
            'last_update': None,
            'esp_last_seen': None,
            'plc_last_seen': None
        }
        self.latest_health_data = {
            'overall_health_score': 0,
            'electrical_health': 0,
            'thermal_health': 0,
            'mechanical_health': 0,
            'predictive_health': 0,
            'efficiency_score': 0,
            'status': 'No Data',
            'status_class': 'secondary',
            'issues': {}
        }
        
        # Setup routes and websocket events
        setup_routes(self.app, self)
        setup_websocket_events(self.socketio, self)
        
        logger.info("Motor Monitoring System initialized")
    
    def start_background_tasks(self):
        """Start all background monitoring tasks"""
        # PLC data collection
        plc_thread = threading.Thread(target=self._plc_data_collector, daemon=True)
        plc_thread.start()
        
        # Health analysis
        health_thread = threading.Thread(target=self._health_analysis_task, daemon=True)
        health_thread.start()
        
        # Connection monitoring
        monitor_thread = threading.Thread(target=self._connection_monitor, daemon=True)
        monitor_thread.start()
        
        logger.info("Background tasks started")
    
    def _plc_data_collector(self):
        """Background task for PLC data collection"""
        import time
        from datetime import datetime
        
        while True:
            try:
                plc_data = self.plc_manager.read_data()
                current_time = datetime.now()
                
                if plc_data and plc_data.get('plc_connected', False):
                    self.latest_data.update(plc_data)
                    self.system_status['plc_connected'] = True
                    self.system_status['plc_last_seen'] = current_time.isoformat()
                    logger.debug(f"PLC data updated: {plc_data}")
                else:
                    if self.system_status['plc_connected']:
                        logger.warning("PLC connection lost")
                    self.system_status['plc_connected'] = False
                    self.latest_data['plc_connected'] = False
                    self.latest_data['plc_motor_temp'] = None
                    self.latest_data['plc_motor_voltage'] = None
            except Exception as e:
                logger.error(f"Error in PLC data collection: {e}")
                self.system_status['plc_connected'] = False
            
            time.sleep(5)
    
    def _health_analysis_task(self):
        """Background task for AI health analysis"""
        import time
        
        while True:
            try:
                if len(self.latest_data) > 0:
                    # Get recent data for analysis
                    recent_data = self.db_manager.get_recent_data(hours=2)
                    
                    # Calculate comprehensive health
                    self.latest_health_data = self.health_analyzer.calculate_comprehensive_health(
                        self.latest_data, recent_data
                    )
                    
                    # Generate recommendations
                    recommendations = self.health_analyzer.generate_recommendations(
                        self.latest_health_data, self.system_status
                    )
                    
                    # Emit updates via WebSocket
                    self.socketio.emit('health_update', self.latest_health_data)
                    self.socketio.emit('recommendations_update', recommendations)
                    
                    # Save critical alerts
                    self._save_critical_alerts(recommendations)
                    
                    self.system_status['ai_model_status'] = 'Active'
                else:
                    self.system_status['ai_model_status'] = 'Waiting for data'
            except Exception as e:
                logger.error(f"Error in health analysis: {e}")
                self.system_status['ai_model_status'] = 'Error'
            
            time.sleep(15)
    
    def _connection_monitor(self):
        """Background task for connection monitoring"""
        import time
        from datetime import datetime
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check ESP timeout
                if self.system_status['esp_last_seen']:
                    esp_last_seen = datetime.fromisoformat(self.system_status['esp_last_seen'])
                    esp_timeout = (current_time - esp_last_seen).total_seconds()
                    
                    if esp_timeout > self.config.ESP_TIMEOUT:
                        if self.system_status['esp_connected']:
                            logger.warning(f"ESP timeout ({esp_timeout:.0f}s)")
                            self.system_status['esp_connected'] = False
                            self._clear_esp_data()
                            self.socketio.emit('connection_lost', {
                                'component': 'ESP',
                                'message': 'ESP connection timeout',
                                'timeout': esp_timeout
                            })
                
                # Check PLC timeout
                if self.system_status['plc_last_seen']:
                    plc_last_seen = datetime.fromisoformat(self.system_status['plc_last_seen'])
                    plc_timeout = (current_time - plc_last_seen).total_seconds()
                    
                    if plc_timeout > self.config.PLC_TIMEOUT:
                        if self.system_status['plc_connected']:
                            logger.warning(f"PLC timeout ({plc_timeout:.0f}s)")
                            self.system_status['plc_connected'] = False
                            self._clear_plc_data()
                            self.socketio.emit('connection_lost', {
                                'component': 'PLC',
                                'message': 'PLC connection timeout',
                                'timeout': plc_timeout
                            })
                
                self.socketio.emit('status_update', self.system_status)
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
            
            time.sleep(self.config.DATA_CLEANUP_INTERVAL)
    
    def _clear_esp_data(self):
        """Clear ESP-related data on timeout"""
        esp_keys = ['esp_current', 'esp_voltage', 'esp_rpm', 'env_temp_c', 
                   'env_humidity', 'env_temp_f', 'heat_index_c', 'heat_index_f',
                   'relay1_status', 'relay2_status', 'relay3_status', 'combined_status']
        
        for key in esp_keys:
            if key in self.latest_data:
                self.latest_data[key] = None
    
    def _clear_plc_data(self):
        """Clear PLC-related data on timeout"""
        self.latest_data['plc_motor_temp'] = None
        self.latest_data['plc_motor_voltage'] = None
        self.latest_data['plc_connected'] = False
    
    def _save_critical_alerts(self, recommendations):
        """Save critical alerts to database"""
        from datetime import datetime, timedelta
        
        for rec in recommendations:
            if rec['severity'] in ['CRITICAL', 'HIGH'] and rec['confidence'] > 0.8:
                # Check if similar alert exists
                existing = self.db_manager.get_similar_alert(
                    rec['type'], minutes=30
                )
                
                if not existing:
                    self.db_manager.save_alert(rec)
                    self.socketio.emit('maintenance_alert', {
                        'type': rec['type'],
                        'severity': rec['severity'],
                        'message': rec['description'],
                        'confidence': rec['confidence']
                    })
    
    def run(self):
        """Run the application"""
        logger.info("Starting AI Motor Monitoring System v4.0")
        logger.info("=== Modular Architecture ===")
        logger.info(f"PLC: {self.config.PLC_IP}:{self.config.PLC_PORT}")
        logger.info(f"Server: {self.config.FLASK_HOST}:{self.config.FLASK_PORT}")
        
        # Initialize database
        self.db_manager.initialize()
        
        # Connect to PLC
        self.plc_manager.connect()
        
        # Start background tasks
        self.start_background_tasks()
        
        try:
            # Run Flask application
            self.socketio.run(
                self.app,
                host=self.config.FLASK_HOST,
                port=self.config.FLASK_PORT,
                debug=self.config.DEBUG,
                use_reloader=False
            )
        except KeyboardInterrupt:
            logger.info("Shutting down system...")
            self.plc_manager.disconnect()
        except Exception as e:
            logger.error(f"Application error: {e}")
            self.plc_manager.disconnect()

if __name__ == '__main__':
    system = MotorMonitoringSystem()
    system.run()
