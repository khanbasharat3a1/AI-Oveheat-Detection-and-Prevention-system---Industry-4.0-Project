"""
Database Manager
Handles all database operations
"""

import os
import csv
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, SensorData, MaintenanceLog, SystemEvents

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.engine = create_engine(config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"Database Manager initialized: {config.DATABASE_URL}")
    
    def initialize(self):
        """Initialize database tables"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.Session()
    
    def save_sensor_data(self, data: Dict, connection_status: Dict = None) -> bool:
        """Save sensor data to database"""
        try:
            session = self.get_session()
            
            # Calculate power consumption
            current = data.get('esp_current', 0) or 0
            voltage = data.get('esp_voltage', 0) or data.get('plc_motor_voltage', 0) or 0
            power_consumption = (current * voltage) / 1000 if current and voltage else 0
            
            sensor_reading = SensorData(
                esp_current=data.get('esp_current'),
                esp_voltage=data.get('esp_voltage'),
                esp_rpm=data.get('esp_rpm'),
                env_temp_c=data.get('env_temp_c'),
                env_humidity=data.get('env_humidity'),
                env_temp_f=data.get('env_temp_f'),
                heat_index_c=data.get('heat_index_c'),
                heat_index_f=data.get('heat_index_f'),
                relay1_status=data.get('relay1_status'),
                relay2_status=data.get('relay2_status'),
                relay3_status=data.get('relay3_status'),
                combined_status=data.get('combined_status'),
                plc_motor_temp=data.get('plc_motor_temp'),
                plc_motor_voltage=data.get('plc_motor_voltage'),
                esp_connected=data.get('esp_connected', False),
                plc_connected=data.get('plc_connected', False),
                overall_health_score=data.get('overall_health_score'),
                electrical_health=data.get('electrical_health'),
                thermal_health=data.get('thermal_health'),
                mechanical_health=data.get('mechanical_health'),
                predictive_health=data.get('predictive_health'),
                efficiency_score=data.get('efficiency_score'),
                power_consumption=power_consumption
            )
            
            session.add(sensor_reading)
            session.commit()
            session.close()
            
            # Export to CSV
            self.export_to_csv(data, power_consumption)
            return True
            
        except Exception as e:
            logger.error(f"Error saving sensor data: {e}")
            return False
    
    def export_to_csv(self, data: Dict, power: float):
        """Export data to CSV file"""
        try:
            file_exists = os.path.isfile(self.config.CSV_EXPORT_PATH)
            with open(self.config.CSV_EXPORT_PATH, 'a', newline='') as csvfile:
                fieldnames = ['timestamp', 'esp_current', 'esp_voltage', 'esp_rpm', 
                             'env_temp_c', 'env_humidity', 'plc_motor_temp', 
                             'plc_motor_voltage', 'power_consumption', 
                             'overall_health_score', 'electrical_health', 'thermal_health',
                             'mechanical_health', 'predictive_health', 'efficiency_score']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'esp_current': data.get('esp_current', 0),
                    'esp_voltage': data.get('esp_voltage', 0),
                    'esp_rpm': data.get('esp_rpm', 0),
                    'env_temp_c': data.get('env_temp_c', 0),
                    'env_humidity': data.get('env_humidity', 0),
                    'plc_motor_temp': data.get('plc_motor_temp', 0),
                    'plc_motor_voltage': data.get('plc_motor_voltage', 0),
                    'power_consumption': power,
                    'overall_health_score': data.get('overall_health_score', 0),
                    'electrical_health': data.get('electrical_health', 0),
                    'thermal_health': data.get('thermal_health', 0),
                    'mechanical_health': data.get('mechanical_health', 0),
                    'predictive_health': data.get('predictive_health', 0),
                    'efficiency_score': data.get('efficiency_score', 0)
                })
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def get_recent_data(self, hours: int = 24) -> pd.DataFrame:
        """Get recent sensor data"""
        try:
            session = self.get_session()
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = session.query(SensorData).filter(
                SensorData.timestamp >= cutoff_time
            ).order_by(SensorData.timestamp.desc())
            
            data = pd.read_sql(query.statement, self.engine)
            session.close()
            return data
        except Exception as e:
            logger.error(f"Error retrieving recent data: {e}")
            return pd.DataFrame()
    
    def get_maintenance_alerts(self) -> List[Dict]:
        """Get active maintenance alerts"""
        try:
            session = self.get_session()
            alerts = session.query(MaintenanceLog).filter(
                MaintenanceLog.acknowledged == False
            ).order_by(MaintenanceLog.timestamp.desc()).limit(10).all()
            
            result = []
            for alert in alerts:
                result.append({
                    'id': alert.id,
                    'timestamp': alert.timestamp.isoformat(),
                    'type': alert.alert_type,
                    'category': alert.category,
                    'severity': alert.severity,
                    'priority': alert.priority,
                    'description': alert.description,
                    'confidence': alert.prediction_confidence,
                    'action': alert.recommended_action
                })
            
            session.close()
            return result
        except Exception as e:
            logger.error(f"Error retrieving maintenance alerts: {e}")
            return []
    
    def save_alert(self, recommendation: Dict) -> bool:
        """Save maintenance alert to database"""
        try:
            session = self.get_session()
            alert = MaintenanceLog(
                alert_type=recommendation['type'],
                category=recommendation['category'],
                severity=recommendation['severity'],
                priority=recommendation['priority'],
                description=recommendation['description'],
                prediction_confidence=recommendation['confidence'],
                recommended_action=recommendation['action']
            )
            session.add(alert)
            session.commit()
            session.close()
            return True
        except Exception as e:
            logger.error(f"Error saving alert: {e}")
            return False
    
    def get_similar_alert(self, alert_type: str, minutes: int = 30) -> bool:
        """Check if similar alert exists within time window"""
        try:
            session = self.get_session()
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            existing = session.query(MaintenanceLog).filter(
                MaintenanceLog.alert_type == alert_type,
                MaintenanceLog.acknowledged == False,
                MaintenanceLog.timestamp > cutoff_time
            ).first()
            
            session.close()
            return existing is not None
        except Exception as e:
            logger.error(f"Error checking similar alert: {e}")
            return False
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge maintenance alert"""
        try:
            session = self.get_session()
            alert = session.query(MaintenanceLog).filter_by(id=alert_id).first()
            if alert:
                alert.acknowledged = True
                session.commit()
                session.close()
                return True
            else:
                session.close()
                return False
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    def log_system_event(self, event_type: str, component: str, message: str, severity: str = 'INFO') -> bool:
        """Log system event"""
        try:
            session = self.get_session()
            event = SystemEvents(
                event_type=event_type,
                component=component,
                message=message,
                severity=severity
            )
            session.add(event)
            session.commit()
            session.close()
            return True
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
            return False
