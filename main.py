#!/usr/bin/env python3
"""
AI-Enabled Industrial Motor Health & Environment Monitoring System
Complete Version with FX5U PLC Support
Version 3.1 - Final Implementation
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
from collections import deque
import csv
import sqlite3

# Flask and web components
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# Database
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ML and AI components
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# PLC Communication
import pymcprotocol

# Configuration and setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SystemConfig:
    # FX5U PLC Configuration
    PLC_IP: str = '192.168.3.39'     # Change this to your FX5U IP
    PLC_PORT: int = 5007             # FX5U MC protocol port
    
    # Server Configuration
    FLASK_HOST: str = '0.0.0.0'
    FLASK_PORT: int = 5000
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = 'sqlite:///motor_monitoring.db'
    CSV_EXPORT_PATH: str = 'sensor_data.csv'
    MODEL_PATH: str = 'models/'
    
    # Connection Timeouts (in seconds)
    ESP_TIMEOUT: int = 30
    PLC_TIMEOUT: int = 60
    DATA_CLEANUP_INTERVAL: int = 10
    
    # OPTIMAL VALUES - 24V Motor System
    OPTIMAL_MOTOR_TEMP: float = 40.0
    OPTIMAL_VOLTAGE: float = 24.0
    OPTIMAL_CURRENT: float = 6.25
    OPTIMAL_DHT_TEMP: float = 24.0
    OPTIMAL_DHT_HUMIDITY: float = 40.0
    OPTIMAL_RPM: float = 2750.0
    
    # THRESHOLDS
    MOTOR_TEMP_EXCELLENT: float = 35.0
    MOTOR_TEMP_GOOD: float = 40.0
    MOTOR_TEMP_WARNING: float = 50.0
    MOTOR_TEMP_CRITICAL: float = 60.0
    
    VOLTAGE_MIN_CRITICAL: float = 20.0
    VOLTAGE_MIN_WARNING: float = 22.0
    VOLTAGE_MAX_WARNING: float = 26.0
    VOLTAGE_MAX_CRITICAL: float = 28.0
    
    CURRENT_MIN_WARNING: float = 4.0
    CURRENT_OPTIMAL_MIN: float = 5.0
    CURRENT_OPTIMAL_MAX: float = 7.5
    CURRENT_MAX_WARNING: float = 9.0
    CURRENT_MAX_CRITICAL: float = 12.0
    
    RPM_MIN_CRITICAL: float = 2400.0
    RPM_MIN_WARNING: float = 2600.0
    RPM_MAX_WARNING: float = 2900.0
    RPM_MAX_CRITICAL: float = 3100.0
    
    DHT_TEMP_MAX_WARNING: float = 30.0
    DHT_TEMP_MAX_CRITICAL: float = 35.0
    DHT_HUMIDITY_MIN_WARNING: float = 30.0
    DHT_HUMIDITY_MAX_WARNING: float = 70.0
    DHT_HUMIDITY_MAX_CRITICAL: float = 80.0

config = SystemConfig()

# =============================================================================
# DATABASE MODELS
# =============================================================================

Base = declarative_base()

class SensorData(Base):
    __tablename__ = 'sensor_data'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # ESP/Arduino Data
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

# =============================================================================
# AI HEALTH ANALYZER
# =============================================================================

class MotorHealthAnalyzer:
    def __init__(self):
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'esp_current', 'esp_voltage', 'esp_rpm', 'env_temp_c', 
            'env_humidity', 'plc_motor_temp', 'plc_motor_voltage'
        ]
    
    def calculate_electrical_health(self, data: Dict) -> Tuple[float, List[str]]:
        score = 100.0
        issues = []
        
        voltage = data.get('esp_voltage') or data.get('plc_motor_voltage')
        current = data.get('esp_current')
        
        if voltage is None and current is None:
            return 0.0, ["No electrical data available"]
        
        # Voltage assessment
        if voltage is not None:
            if voltage < config.VOLTAGE_MIN_CRITICAL:
                score -= 40
                issues.append(f"Critical undervoltage: {voltage:.1f}V")
            elif voltage < config.VOLTAGE_MIN_WARNING:
                score -= 20
                issues.append(f"Low voltage: {voltage:.1f}V")
            elif voltage > config.VOLTAGE_MAX_CRITICAL:
                score -= 40
                issues.append(f"Critical overvoltage: {voltage:.1f}V")
            elif voltage > config.VOLTAGE_MAX_WARNING:
                score -= 20
                issues.append(f"High voltage: {voltage:.1f}V")
        
        # Current assessment
        if current is not None:
            if current < config.CURRENT_MIN_WARNING:
                score -= 30
                issues.append(f"Motor underloaded: {current:.1f}A")
            elif current > config.CURRENT_MAX_CRITICAL:
                score -= 50
                issues.append(f"Critical overcurrent: {current:.1f}A")
            elif current > config.CURRENT_MAX_WARNING:
                score -= 25
                issues.append(f"Motor overloaded: {current:.1f}A")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_thermal_health(self, data: Dict) -> Tuple[float, List[str]]:
        score = 100.0
        issues = []
        
        motor_temp = data.get('plc_motor_temp')
        env_temp = data.get('env_temp_c')
        humidity = data.get('env_humidity')
        
        if motor_temp is None and env_temp is None:
            return 0.0, ["No thermal data available"]
        
        # Motor temperature assessment
        if motor_temp is not None:
            if motor_temp > config.MOTOR_TEMP_CRITICAL:
                score -= 50
                issues.append(f"Critical motor temperature: {motor_temp:.1f}°C")
            elif motor_temp > config.MOTOR_TEMP_WARNING:
                score -= 30
                issues.append(f"High motor temperature: {motor_temp:.1f}°C")
            elif motor_temp > config.MOTOR_TEMP_GOOD:
                score -= 15
                issues.append(f"Elevated motor temperature: {motor_temp:.1f}°C")
        
        # Environmental assessment
        if env_temp is not None:
            if env_temp > config.DHT_TEMP_MAX_CRITICAL:
                score -= 25
                issues.append(f"Critical ambient temperature: {env_temp:.1f}°C")
            elif env_temp > config.DHT_TEMP_MAX_WARNING:
                score -= 15
                issues.append(f"High ambient temperature: {env_temp:.1f}°C")
        
        if humidity is not None:
            if humidity > config.DHT_HUMIDITY_MAX_CRITICAL:
                score -= 20
                issues.append(f"Critical humidity: {humidity:.1f}%")
            elif humidity > config.DHT_HUMIDITY_MAX_WARNING:
                score -= 10
                issues.append(f"High humidity: {humidity:.1f}%")
            elif humidity < config.DHT_HUMIDITY_MIN_WARNING:
                score -= 5
                issues.append(f"Low humidity: {humidity:.1f}%")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_mechanical_health(self, data: Dict) -> Tuple[float, List[str]]:
        score = 100.0
        issues = []
        
        rpm = data.get('esp_rpm')
        current = data.get('esp_current')
        
        if rpm is None:
            return 0.0, ["No RPM data available"]
        
        # RPM assessment
        if rpm < config.RPM_MIN_CRITICAL:
            score -= 50
            issues.append(f"Critical low RPM: {rpm:.0f}")
        elif rpm < config.RPM_MIN_WARNING:
            score -= 30
            issues.append(f"Low RPM: {rpm:.0f}")
        elif rpm > config.RPM_MAX_CRITICAL:
            score -= 50
            issues.append(f"Critical high RPM: {rpm:.0f}")
        elif rpm > config.RPM_MAX_WARNING:
            score -= 30
            issues.append(f"High RPM: {rpm:.0f}")
        
        # Load balance check
        if current is not None and rpm > 0:
            expected_current = (rpm / config.OPTIMAL_RPM) * config.OPTIMAL_CURRENT
            current_deviation = abs(current - expected_current) / expected_current
            
            if current_deviation > 0.5:
                score -= 20
                issues.append(f"Current/RPM imbalance detected")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_predictive_health(self, recent_data: pd.DataFrame) -> Tuple[float, List[str]]:
        score = 100.0
        issues = []
        
        if len(recent_data) < 5:
            return 50.0, ["Insufficient data for prediction"]
        
        try:
            # Temperature trend analysis
            if 'plc_motor_temp' in recent_data.columns:
                temp_trend = recent_data['plc_motor_temp'].dropna().tail(10)
                if len(temp_trend) >= 5:
                    temp_slope = np.polyfit(range(len(temp_trend)), temp_trend, 1)[0]
                    if temp_slope > 1.0:
                        score -= 30
                        issues.append(f"Rising temperature trend: +{temp_slope:.1f}°C/reading")
            
            # Current stability analysis
            if 'esp_current' in recent_data.columns:
                current_trend = recent_data['esp_current'].dropna().tail(10)
                if len(current_trend) >= 5:
                    current_slope = np.polyfit(range(len(current_trend)), current_trend, 1)[0]
                    if abs(current_slope) > 0.5:
                        score -= 25
                        issues.append(f"Current instability: ±{abs(current_slope):.1f}A/reading")
            
            # Health degradation trend
            if 'overall_health_score' in recent_data.columns:
                health_trend = recent_data['overall_health_score'].dropna().tail(20)
                if len(health_trend) >= 10:
                    health_slope = np.polyfit(range(len(health_trend)), health_trend, 1)[0]
                    if health_slope < -1.0:
                        score -= 35
                        issues.append(f"Health degradation trend: {health_slope:.1f} points/reading")
        
        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
            issues.append("Predictive analysis error")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_comprehensive_health(self, current_data: Dict, recent_data: pd.DataFrame = None) -> Dict:
        # Calculate individual health components
        electrical_score, electrical_issues = self.calculate_electrical_health(current_data)
        thermal_score, thermal_issues = self.calculate_thermal_health(current_data)
        mechanical_score, mechanical_issues = self.calculate_mechanical_health(current_data)
        
        if recent_data is not None and len(recent_data) > 0:
            predictive_score, predictive_issues = self.calculate_predictive_health(recent_data)
        else:
            predictive_score, predictive_issues = 50.0, ["Limited historical data"]
        
        # Calculate overall health score (weighted average)
        overall_score = (
            electrical_score * 0.30 +    # 30% weight
            thermal_score * 0.35 +       # 35% weight
            mechanical_score * 0.25 +    # 25% weight
            predictive_score * 0.10      # 10% weight
        )
        
        # Calculate efficiency score
        efficiency_score = self.calculate_efficiency_score(current_data)
        
        # Determine overall status
        if overall_score >= 90:
            status = "Excellent"
            status_class = "success"
        elif overall_score >= 75:
            status = "Good"
            status_class = "info"
        elif overall_score >= 60:
            status = "Warning"
            status_class = "warning"
        else:
            status = "Critical"
            status_class = "danger"
        
        return {
            'overall_health_score': round(overall_score, 1),
            'electrical_health': round(electrical_score, 1),
            'thermal_health': round(thermal_score, 1),
            'mechanical_health': round(mechanical_score, 1),
            'predictive_health': round(predictive_score, 1),
            'efficiency_score': round(efficiency_score, 1),
            'status': status,
            'status_class': status_class,
            'issues': {
                'electrical': electrical_issues,
                'thermal': thermal_issues,
                'mechanical': mechanical_issues,
                'predictive': predictive_issues
            }
        }
    
    def calculate_efficiency_score(self, data: Dict) -> float:
        voltage = data.get('esp_voltage') or data.get('plc_motor_voltage', 0)
        current = data.get('esp_current', 0)
        rpm = data.get('esp_rpm', 0)
        
        if not all([voltage, current, rpm]):
            return 0.0
        
        # Calculate efficiency metrics
        rpm_efficiency = min(100, (rpm / config.OPTIMAL_RPM) * 100)
        
        actual_power = voltage * current / 1000
        theoretical_power = config.OPTIMAL_VOLTAGE * config.OPTIMAL_CURRENT / 1000
        power_efficiency = min(100, (theoretical_power / actual_power) * 100) if actual_power > 0 else 0
        
        overall_efficiency = (rpm_efficiency + power_efficiency) / 2
        return max(0.0, min(100.0, overall_efficiency))
    
    def generate_recommendations(self, health_data: Dict, connection_status: Dict) -> List[Dict]:
        recommendations = []
        
        # Connection alerts
        if not connection_status.get('esp_connected', False):
            recommendations.append({
                'type': 'Connection Alert',
                'category': 'System',
                'severity': 'HIGH',
                'priority': 'HIGH',
                'title': 'ESP/Arduino Disconnected',
                'description': 'ESP sensor module not responding',
                'action': 'Check ESP power and network connectivity',
                'confidence': 1.0
            })
        
        if not connection_status.get('plc_connected', False):
            recommendations.append({
                'type': 'Connection Alert',
                'category': 'System',
                'severity': 'HIGH',
                'priority': 'HIGH',
                'title': 'FX5U PLC Disconnected',
                'description': 'FX5U PLC not responding on port 5007',
                'action': 'Check FX5U network and MC protocol settings',
                'confidence': 1.0
            })
        
        # Health-based recommendations
        overall_score = health_data.get('overall_health_score', 0)
        
        if overall_score < 60:
            recommendations.append({
                'type': 'Critical Alert',
                'category': 'Health',
                'severity': 'CRITICAL',
                'priority': 'CRITICAL',
                'title': 'Motor Health Critical',
                'description': f'Overall health: {overall_score}% - Immediate attention required',
                'action': 'Stop motor and perform immediate inspection',
                'confidence': 0.95
            })
        
        if health_data.get('electrical_health', 0) < 70:
            recommendations.append({
                'type': 'Electrical Warning',
                'category': 'Electrical',
                'severity': 'MEDIUM',
                'priority': 'MEDIUM',
                'title': 'Electrical System Issues',
                'description': 'Voltage or current outside optimal range',
                'action': 'Check 24V motor connections and measure with multimeter',
                'confidence': 0.8
            })
        
        if health_data.get('thermal_health', 0) < 70:
            recommendations.append({
                'type': 'Temperature Warning',
                'category': 'Thermal',
                'severity': 'MEDIUM',
                'priority': 'MEDIUM',
                'title': 'Thermal Issues',
                'description': 'Temperature above optimal levels',
                'action': 'Improve ventilation and check cooling system',
                'confidence': 0.85
            })
        
        if health_data.get('mechanical_health', 0) < 70:
            recommendations.append({
                'type': 'Mechanical Warning',
                'category': 'Mechanical',
                'severity': 'MEDIUM',
                'priority': 'MEDIUM',
                'title': 'Mechanical Issues',
                'description': 'RPM or load outside optimal range',
                'action': 'Inspect bearings and check coupling alignment',
                'confidence': 0.8
            })
        
        # Sort by priority
        priority_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations[:10]

# =============================================================================
# DATA MANAGER
# =============================================================================

class DataManager:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.health_analyzer = MotorHealthAnalyzer()
        
    def get_session(self) -> Session:
        return self.Session()
    
    def save_sensor_data(self, data: Dict, connection_status: Dict = None) -> bool:
        try:
            session = self.get_session()
            
            # Get recent data for analysis
            recent_data = self.get_recent_data(hours=2)
            
            # Calculate health scores
            health_data = self.health_analyzer.calculate_comprehensive_health(data, recent_data)
            
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
                overall_health_score=health_data['overall_health_score'],
                electrical_health=health_data['electrical_health'],
                thermal_health=health_data['thermal_health'],
                mechanical_health=health_data['mechanical_health'],
                predictive_health=health_data['predictive_health'],
                efficiency_score=health_data['efficiency_score'],
                power_consumption=power_consumption
            )
            
            session.add(sensor_reading)
            session.commit()
            session.close()
            
            # Export to CSV
            self.export_to_csv(data, health_data, power_consumption)
            return True
            
        except Exception as e:
            logger.error(f"Error saving sensor data: {e}")
            return False
    
    def export_to_csv(self, data: Dict, health_data: Dict, power: float):
        try:
            file_exists = os.path.isfile(config.CSV_EXPORT_PATH)
            with open(config.CSV_EXPORT_PATH, 'a', newline='') as csvfile:
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
                    'overall_health_score': health_data['overall_health_score'],
                    'electrical_health': health_data['electrical_health'],
                    'thermal_health': health_data['thermal_health'],
                    'mechanical_health': health_data['mechanical_health'],
                    'predictive_health': health_data['predictive_health'],
                    'efficiency_score': health_data['efficiency_score']
                })
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
    
    def get_recent_data(self, hours: int = 24) -> pd.DataFrame:
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

# =============================================================================
# FX5U PLC MANAGER
# =============================================================================

class FX5UPLCManager:
    def __init__(self):
        self.mc = pymcprotocol.Type3E()
        self.connected = False
        self.last_data = {}
        
    def connect(self) -> bool:
        try:
            if self.mc.connect(config.PLC_IP, config.PLC_PORT):
                self.connected = True
                logger.info(f"FX5U PLC connected: {config.PLC_IP}:{config.PLC_PORT}")
                return True
            else:
                self.connected = False
                logger.error("Failed to connect to FX5U PLC")
                return False
        except Exception as e:
            self.connected = False
            logger.error(f"FX5U PLC connection error: {e}")
            return False
    
    def convert_voltage(self, raw_value: int) -> float:
        """Convert D100 to voltage (24V system)"""
        if raw_value <= 0:
            return 0.0
        
        # For 24V system: scale raw value to actual voltage
        # Assuming max raw value ~4095 represents ~30V range
        voltage = (raw_value / 4095.0) * 30.0
        return round(voltage, 1)
    
    def convert_temperature(self, raw_value: int) -> float:
        """Convert D102 to temperature using: Temperature (°C) = 0.05175 × Raw Value"""
        if raw_value <= 0:
            return 0.0
        
        temperature = 0.05175 * raw_value
        return round(temperature, 1)
    
    def read_data(self) -> Dict:
        if not self.connected:
            if not self.connect():
                return {'plc_connected': False}
        
        try:
            # Read FX5U registers
            raw_d100 = self.mc.batchread_wordunits(headdevice="D100", readsize=1)[0]  # Voltage
            raw_d102 = self.mc.batchread_wordunits(headdevice="D102", readsize=1)[0]  # Temperature
            
            # Convert values
            motor_voltage = self.convert_voltage(raw_d100)
            motor_temp = self.convert_temperature(raw_d102)
            
            self.last_data = {
                'plc_motor_temp': motor_temp,
                'plc_motor_voltage': motor_voltage,
                'plc_connected': True,
                'raw_d100': raw_d100,
                'raw_d102': raw_d102
            }
            
            logger.debug(f"FX5U: D100({raw_d100})->  {motor_voltage}V, D102({raw_d102})-> {motor_temp}°C")
            return self.last_data
            
        except Exception as e:
            logger.error(f"Error reading FX5U data: {e}")
            self.connected = False
            return {'plc_connected': False}
    
    def disconnect(self):
        try:
            if self.connected:
                self.mc.close()
                self.connected = False
                logger.info("FX5U PLC disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting FX5U: {e}")

# =============================================================================
# FLASK APPLICATION
# =============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'motor_monitoring_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
data_manager = DataManager()
plc_manager = FX5UPLCManager()
latest_data = {}
system_status = {
    'esp_connected': False,
    'plc_connected': False,
    'ai_model_status': 'Initializing',
    'last_update': None,
    'esp_last_seen': None,
    'plc_last_seen': None
}

latest_health_data = {
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

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

def plc_data_collector():
    """FX5U data collection task"""
    while True:
        try:
            plc_data = plc_manager.read_data()
            current_time = datetime.now()
            
            if plc_data and plc_data.get('plc_connected', False):
                latest_data.update(plc_data)
                system_status['plc_connected'] = True
                system_status['plc_last_seen'] = current_time.isoformat()
            else:
                if system_status['plc_connected']:
                    logger.warning("FX5U PLC connection failed")
                system_status['plc_connected'] = False
                latest_data['plc_connected'] = False
                latest_data['plc_motor_temp'] = None
                latest_data['plc_motor_voltage'] = None
        except Exception as e:
            logger.error(f"Error in FX5U data collection: {e}")
            system_status['plc_connected'] = False
        
        time.sleep(5)

def data_analysis_task():
    """AI analysis task"""
    global latest_health_data
    
    while True:
        try:
            recent_data = data_manager.get_recent_data(hours=2)
            
            if len(latest_data) > 0:
                latest_health_data = data_manager.health_analyzer.calculate_comprehensive_health(
                    latest_data, recent_data
                )
                
                recommendations = data_manager.health_analyzer.generate_recommendations(
                    latest_health_data, system_status
                )
                
                socketio.emit('health_update', latest_health_data)
                socketio.emit('recommendations_update', recommendations)
                
                # Save critical alerts
                session = data_manager.get_session()
                for rec in recommendations:
                    if rec['severity'] in ['CRITICAL', 'HIGH'] and rec['confidence'] > 0.8:
                        existing = session.query(MaintenanceLog).filter(
                            MaintenanceLog.alert_type == rec['type'],
                            MaintenanceLog.acknowledged == False,
                            MaintenanceLog.timestamp > datetime.utcnow() - timedelta(minutes=30)
                        ).first()
                        
                        if not existing:
                            alert = MaintenanceLog(
                                alert_type=rec['type'],
                                category=rec['category'],
                                severity=rec['severity'],
                                priority=rec['priority'],
                                description=rec['description'],
                                prediction_confidence=rec['confidence'],
                                recommended_action=rec['action']
                            )
                            session.add(alert)
                            
                            socketio.emit('maintenance_alert', {
                                'type': rec['type'],
                                'severity': rec['severity'],
                                'message': rec['description'],
                                'confidence': rec['confidence']
                            })
                
                session.commit()
                session.close()
                system_status['ai_model_status'] = 'Active'
            else:
                system_status['ai_model_status'] = 'Waiting for data'
            
        except Exception as e:
            logger.error(f"Error in data analysis: {e}")
            system_status['ai_model_status'] = 'Error'
        
        time.sleep(15)

def connection_monitor():
    """Connection monitoring task"""
    while True:
        try:
            current_time = datetime.now()
            
            # ESP timeout check
            if system_status['esp_last_seen']:
                esp_last_seen = datetime.fromisoformat(system_status['esp_last_seen'])
                esp_timeout = (current_time - esp_last_seen).total_seconds()
                
                if esp_timeout > config.ESP_TIMEOUT:
                    if system_status['esp_connected']:
                        logger.warning(f"ESP timeout ({esp_timeout:.0f}s)")
                        system_status['esp_connected'] = False
                        
                        esp_keys = ['esp_current', 'esp_voltage', 'esp_rpm', 'env_temp_c', 
                                  'env_humidity', 'env_temp_f', 'heat_index_c', 'heat_index_f',
                                  'relay1_status', 'relay2_status', 'relay3_status', 'combined_status']
                        
                        for key in esp_keys:
                            if key in latest_data:
                                latest_data[key] = None
                        
                        socketio.emit('connection_lost', {
                            'component': 'ESP',
                            'message': 'ESP connection timeout',
                            'timeout': esp_timeout
                        })
            
            # FX5U timeout check
            if system_status['plc_last_seen']:
                plc_last_seen = datetime.fromisoformat(system_status['plc_last_seen'])
                plc_timeout = (current_time - plc_last_seen).total_seconds()
                
                if plc_timeout > config.PLC_TIMEOUT:
                    if system_status['plc_connected']:
                        logger.warning(f"FX5U timeout ({plc_timeout:.0f}s)")
                        system_status['plc_connected'] = False
                        
                        latest_data['plc_motor_temp'] = None
                        latest_data['plc_motor_voltage'] = None
                        latest_data['plc_connected'] = False
                        
                        socketio.emit('connection_lost', {
                            'component': 'PLC',
                            'message': 'FX5U PLC connection timeout',
                            'timeout': plc_timeout
                        })
            
            socketio.emit('status_update', system_status)
            
        except Exception as e:
            logger.error(f"Error in connection monitor: {e}")
        
        time.sleep(config.DATA_CLEANUP_INTERVAL)

# Start background threads
threading.Thread(target=plc_data_collector, daemon=True).start()
threading.Thread(target=data_analysis_task, daemon=True).start()
threading.Thread(target=connection_monitor, daemon=True).start()

# =============================================================================
# FLASK ROUTES
# =============================================================================

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/send-data', methods=['POST'])
def receive_esp_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        current_time = datetime.now()
        
        esp_data = {
            'esp_current': float(data.get('VAL1', 0)) if data.get('VAL1') and data.get('VAL1') != '0' else None,
            'esp_voltage': float(data.get('VAL2', 0)) if data.get('VAL2') and data.get('VAL2') != '0' else None,
            'esp_rpm': float(data.get('VAL3', 0)) if data.get('VAL3') and data.get('VAL3') != '0' else None,
            'env_temp_c': float(data.get('VAL4', 0)) if data.get('VAL4') else None,
            'env_humidity': float(data.get('VAL5', 0)) if data.get('VAL5') else None,
            'env_temp_f': float(data.get('VAL6', 0)) if data.get('VAL6') else None,
            'heat_index_c': float(data.get('VAL7', 0)) if data.get('VAL7') else None,
            'heat_index_f': float(data.get('VAL8', 0)) if data.get('VAL8') else None,
            'relay1_status': data.get('VAL9', 'OFF'),
            'relay2_status': data.get('VAL10', 'OFF'),
            'relay3_status': data.get('VAL11', 'OFF'),
            'combined_status': data.get('VAL12', 'NOR'),
            'esp_connected': True
        }
        
        latest_data.update(esp_data)
        system_status['esp_connected'] = True
        system_status['esp_last_seen'] = current_time.isoformat()
        system_status['last_update'] = current_time.isoformat()
        
        combined_data = {**latest_data}
        data_manager.save_sensor_data(combined_data, system_status)
        
        socketio.emit('sensor_update', combined_data)
        
        logger.info(f"ESP data: Current={esp_data.get('esp_current')}A, Voltage={esp_data.get('esp_voltage')}V, RPM={esp_data.get('esp_rpm')}")
        return jsonify({'status': 'success', 'message': 'Data received'}), 200
        
    except Exception as e:
        logger.error(f"Error processing ESP data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/current-data')
def get_current_data():
    return jsonify({
        'data': latest_data,
        'health': latest_health_data,
        'status': system_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health-details')
def get_health_details():
    return jsonify(latest_health_data)

@app.route('/api/recommendations')
def get_recommendations():
    try:
        recent_data = data_manager.get_recent_data(hours=1)
        recommendations = data_manager.health_analyzer.generate_recommendations(
            latest_health_data, system_status
        )
        return jsonify({'recommendations': recommendations})
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/historical-data')
def get_historical_data():
    hours = request.args.get('hours', 24, type=int)
    try:
        data = data_manager.get_recent_data(hours=hours)
        
        if data.empty:
            return jsonify({'data': [], 'message': 'No data available'})
        
        chart_data = []
        for _, row in data.iterrows():
            chart_data.append({
                'timestamp': row['timestamp'].isoformat() if pd.notnull(row['timestamp']) else None,
                'current': row.get('esp_current', 0),
                'voltage': row.get('esp_voltage', 0),
                'rpm': row.get('esp_rpm', 0),
                'motor_temp': row.get('plc_motor_temp', 0),
                'env_temp': row.get('env_temp_c', 0),
                'humidity': row.get('env_humidity', 0),
                'overall_health_score': row.get('overall_health_score', 0),
                'electrical_health': row.get('electrical_health', 0),
                'thermal_health': row.get('thermal_health', 0),
                'mechanical_health': row.get('mechanical_health', 0),
                'predictive_health': row.get('predictive_health', 0),
                'efficiency_score': row.get('efficiency_score', 0),
                'power': row.get('power_consumption', 0)
            })
        
        return jsonify({'data': chart_data})
        
    except Exception as e:
        logger.error(f"Error retrieving historical data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/maintenance-alerts')
def get_maintenance_alerts():
    try:
        alerts = data_manager.get_maintenance_alerts()
        return jsonify({'alerts': alerts})
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/acknowledge-alert/<int:alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    try:
        session = data_manager.get_session()
        alert = session.query(MaintenanceLog).filter_by(id=alert_id).first()
        if alert:
            alert.acknowledged = True
            session.commit()
            session.close()
            return jsonify({'status': 'success'})
        else:
            session.close()
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/motor-control', methods=['POST'])
def motor_control():
    try:
        command = request.json.get('command')
        logger.info(f"Motor control: {command}")
        
        session = data_manager.get_session()
        event = SystemEvents(
            event_type='Manual Control',
            component='Motor',
            message=f'Command: {command}',
            severity='INFO'
        )
        session.add(event)
        session.commit()
        session.close()
        
        return jsonify({'status': 'success', 'message': f'Command {command} executed'}), 200
    except Exception as e:
        logger.error(f"Error in motor control: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =============================================================================
# WEBSOCKET EVENTS
# =============================================================================

@socketio.on('connect')
def handle_connect():
    emit('status_update', system_status)
    emit('sensor_update', latest_data)
    emit('health_update', latest_health_data)
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    emit('sensor_update', latest_data)
    emit('status_update', system_status)
    emit('health_update', latest_health_data)

# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    logger.info("Starting AI Motor Monitoring System v3.1")
    logger.info("FX5U PLC Support with Enhanced Health Analytics")
    
    # Initialize FX5U connection
    plc_manager.connect()
    
    # Create directories
    os.makedirs(config.MODEL_PATH, exist_ok=True)
    
    # Log configuration
    logger.info("=== SYSTEM CONFIGURATION ===")
    logger.info(f"FX5U PLC: {config.PLC_IP}:{config.PLC_PORT}")
    logger.info(f"D100 = Voltage (24V system)")
    logger.info(f"D102 = Temperature (°C = 0.05175 × Raw)")
    logger.info("============================")
    
    # Test conversions
    test_plc = FX5UPLCManager()
    test_voltage = test_plc.convert_voltage(996)
    test_temp = test_plc.convert_temperature(540)
    logger.info(f"Test: D100(996) = {test_voltage}V, D102(540) = {test_temp}°C")
    
    try:
        socketio.run(
            app, 
            host=config.FLASK_HOST, 
            port=config.FLASK_PORT, 
            debug=config.DEBUG,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        plc_manager.disconnect()
    except Exception as e:
        logger.error(f"Startup error: {e}")
        plc_manager.disconnect()
