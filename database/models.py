"""
Database Models
SQLAlchemy models for all database tables
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorData(Base):
    __tablename__ = 'sensor_data'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # ESP/Arduino Sensors
    esp_current = Column(Float)
    esp_voltage = Column(Float)
    esp_rpm = Column(Float)
    env_temp_c = Column(Float)
    env_humidity = Column(Float)
    env_temp_f = Column(Float)
    heat_index_c = Column(Float)
    heat_index_f = Column(Float)
    
    # Relay Status
    relay1_status = Column(String(10))
    relay2_status = Column(String(10))
    relay3_status = Column(String(10))
    combined_status = Column(String(10))
    
    # FX5U PLC Data
    plc_motor_temp = Column(Float)
    plc_motor_voltage = Column(Float)
    
    # Connection Status
    esp_connected = Column(Boolean, default=False)
    plc_connected = Column(Boolean, default=False)
    
    # Health Scores
    overall_health_score = Column(Float)
    electrical_health = Column(Float)
    thermal_health = Column(Float)
    mechanical_health = Column(Float)
    predictive_health = Column(Float)
    efficiency_score = Column(Float)
    power_consumption = Column(Float)

class MaintenanceLog(Base):
    __tablename__ = 'maintenance_log'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String(50))
    severity = Column(String(20))
    category = Column(String(30))
    description = Column(Text)
    prediction_confidence = Column(Float)
    recommended_action = Column(Text)
    priority = Column(String(20))
    acknowledged = Column(Boolean, default=False)

class SystemEvents(Base):
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50))
    component = Column(String(50))
    message = Column(Text)
    severity = Column(String(20))
