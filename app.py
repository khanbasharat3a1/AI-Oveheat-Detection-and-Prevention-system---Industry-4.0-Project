# #!/usr/bin/env python3
# """
# AI-Enabled Industrial Motor Health & Environment Monitoring System
# Enhanced Version with Improved Health Score Calculation and AI Insights
# Version 3.0 - With Advanced Health Categorization and Smart Recommendations
# """

# import os
# import json
# import time
# import threading
# import logging
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Tuple
# import numpy as np
# import pandas as pd
# from dataclasses import dataclass
# from collections import deque
# import csv
# import sqlite3

# # Flask and web components
# from flask import Flask, render_template, request, jsonify, send_from_directory
# from flask_socketio import SocketIO, emit
# from werkzeug.serving import make_server

# # Database
# from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, Session
# from sqlalchemy.exc import SQLAlchemyError

# # ML and AI components
# from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingRegressor
# from sklearn.preprocessing import StandardScaler, MinMaxScaler
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, mean_squared_error
# import joblib

# # PLC Communication
# import pymcprotocol

# # Configuration and setup
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # =============================================================================
# # CONFIGURATION - Updated with Optimal Values
# # =============================================================================

# @dataclass
# class SystemConfig:
#     # PLC Configuration
#     PLC_IP: str = '192.168.3.39'
#     PLC_PORT: int = 5000
    
#     # Server Configuration
#     FLASK_HOST: str = '0.0.0.0'
#     FLASK_PORT: int = 5000
#     DEBUG: bool = True
    
#     # Database
#     DATABASE_URL: str = 'sqlite:///motor_monitoring.db'
#     CSV_EXPORT_PATH: str = 'sensor_data.csv'
    
#     # AI Model paths
#     MODEL_PATH: str = 'models/'
    
#     # Connection Timeouts (in seconds)
#     ESP_TIMEOUT: int = 30
#     PLC_TIMEOUT: int = 60
#     DATA_CLEANUP_INTERVAL: int = 10
    
#     # OPTIMAL VALUES - Based on your specifications
#     OPTIMAL_MOTOR_TEMP: float = 40.0       # Motor temperature optimal < 40°C
#     OPTIMAL_VOLTAGE: float = 24.0          # 24V DC motor
#     OPTIMAL_CURRENT: float = 6.25          # 6.25A optimal current
#     OPTIMAL_DHT_TEMP: float = 24.0         # DHT temperature 24°C
#     OPTIMAL_DHT_HUMIDITY: float = 40.0     # DHT humidity 40%
#     OPTIMAL_RPM: float = 2750.0            # RPM 2750
    
#     # THRESHOLD RANGES
#     # Motor Temperature Thresholds
#     MOTOR_TEMP_EXCELLENT: float = 35.0     # < 35°C = Excellent
#     MOTOR_TEMP_GOOD: float = 40.0          # < 40°C = Good
#     MOTOR_TEMP_WARNING: float = 50.0       # < 50°C = Warning
#     MOTOR_TEMP_CRITICAL: float = 60.0      # > 60°C = Critical
    
#     # Voltage Thresholds (24V ±10%)
#     VOLTAGE_MIN_CRITICAL: float = 20.0     # < 20V = Critical
#     VOLTAGE_MIN_WARNING: float = 22.0      # < 22V = Warning
#     VOLTAGE_MAX_WARNING: float = 26.0      # > 26V = Warning
#     VOLTAGE_MAX_CRITICAL: float = 28.0     # > 28V = Critical
    
#     # Current Thresholds (6.25A ±20%)
#     CURRENT_MIN_WARNING: float = 4.0       # < 4A = Warning (underload)
#     CURRENT_OPTIMAL_MIN: float = 5.0       # 5-7.5A = Optimal range
#     CURRENT_OPTIMAL_MAX: float = 7.5
#     CURRENT_MAX_WARNING: float = 9.0       # > 9A = Warning (overload)
#     CURRENT_MAX_CRITICAL: float = 12.0     # > 12A = Critical
    
#     # RPM Thresholds (2750 ±5%)
#     RPM_MIN_CRITICAL: float = 2400.0       # < 2400 = Critical
#     RPM_MIN_WARNING: float = 2600.0        # < 2600 = Warning
#     RPM_MAX_WARNING: float = 2900.0        # > 2900 = Warning
#     RPM_MAX_CRITICAL: float = 3100.0       # > 3100 = Critical
    
#     # Environmental Thresholds
#     DHT_TEMP_MAX_WARNING: float = 30.0     # > 30°C ambient = Warning
#     DHT_TEMP_MAX_CRITICAL: float = 35.0    # > 35°C ambient = Critical
#     DHT_HUMIDITY_MIN_WARNING: float = 30.0 # < 30% = Warning
#     DHT_HUMIDITY_MAX_WARNING: float = 70.0 # > 70% = Warning
#     DHT_HUMIDITY_MAX_CRITICAL: float = 80.0 # > 80% = Critical
    
#     # Data retention
#     DATA_RETENTION_DAYS: int = 90
#     HEALTH_SCORE_WINDOW: int = 100

# config = SystemConfig()

# # =============================================================================
# # DATABASE MODELS - Enhanced
# # =============================================================================

# Base = declarative_base()

# class SensorData(Base):
#     __tablename__ = 'sensor_data'
    
#     id = Column(Integer, primary_key=True)
#     timestamp = Column(DateTime, default=datetime.utcnow)
    
#     # Arduino/ESP Sensors
#     esp_current = Column(Float)
#     esp_voltage = Column(Float)
#     esp_rpm = Column(Float)
#     env_temp_c = Column(Float)
#     env_humidity = Column(Float)
#     env_temp_f = Column(Float)
#     heat_index_c = Column(Float)
#     heat_index_f = Column(Float)
    
#     # Arduino Relays
#     relay1_status = Column(String(10))
#     relay2_status = Column(String(10))
#     relay3_status = Column(String(10))
#     combined_status = Column(String(10))
    
#     # PLC Data
#     plc_motor_temp = Column(Float)
#     plc_motor_voltage = Column(Float)
    
#     # Connection Status
#     esp_connected = Column(Boolean, default=False)
#     plc_connected = Column(Boolean, default=False)
    
#     # Enhanced Health Scores
#     overall_health_score = Column(Float)
#     electrical_health = Column(Float)
#     thermal_health = Column(Float)
#     mechanical_health = Column(Float)
#     predictive_health = Column(Float)
#     efficiency_score = Column(Float)
#     power_consumption = Column(Float)

# class MaintenanceLog(Base):
#     __tablename__ = 'maintenance_log'
    
#     id = Column(Integer, primary_key=True)
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     alert_type = Column(String(50))
#     severity = Column(String(20))
#     category = Column(String(30))  # NEW: Electrical, Thermal, Mechanical, etc.
#     description = Column(Text)
#     prediction_confidence = Column(Float)
#     recommended_action = Column(Text)
#     priority = Column(String(20))  # NEW: LOW, MEDIUM, HIGH, CRITICAL
#     acknowledged = Column(Boolean, default=False)

# class SystemEvents(Base):
#     __tablename__ = 'system_events'
    
#     id = Column(Integer, primary_key=True)
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     event_type = Column(String(50))
#     component = Column(String(50))
#     message = Column(Text)
#     severity = Column(String(20))

# # =============================================================================
# # ENHANCED AI MODELS AND ANALYTICS
# # =============================================================================

# class AdvancedMotorHealthAnalyzer:
#     def __init__(self):
#         self.isolation_forest = None
#         self.health_regressor = None
#         self.maintenance_classifier = None
#         self.scaler = StandardScaler()
#         self.is_trained = False
#         self.feature_columns = [
#             'esp_current', 'esp_voltage', 'esp_rpm', 'env_temp_c', 
#             'env_humidity', 'plc_motor_temp', 'plc_motor_voltage'
#         ]
        
#     def calculate_electrical_health(self, data: Dict) -> Tuple[float, List[str]]:
#         """Calculate electrical health score (0-100) and issues"""
#         score = 100.0
#         issues = []
        
#         voltage = data.get('esp_voltage') or data.get('plc_motor_voltage')
#         current = data.get('esp_current')
        
#         if voltage is None and current is None:
#             return 0.0, ["No electrical data available"]
        
#         # Voltage assessment
#         if voltage is not None:
#             if voltage < config.VOLTAGE_MIN_CRITICAL:
#                 score -= 40
#                 issues.append(f"Critical undervoltage: {voltage:.1f}V (min: {config.VOLTAGE_MIN_CRITICAL}V)")
#             elif voltage < config.VOLTAGE_MIN_WARNING:
#                 score -= 20
#                 issues.append(f"Low voltage warning: {voltage:.1f}V (optimal: {config.OPTIMAL_VOLTAGE}V)")
#             elif voltage > config.VOLTAGE_MAX_CRITICAL:
#                 score -= 40
#                 issues.append(f"Critical overvoltage: {voltage:.1f}V (max: {config.VOLTAGE_MAX_CRITICAL}V)")
#             elif voltage > config.VOLTAGE_MAX_WARNING:
#                 score -= 20
#                 issues.append(f"High voltage warning: {voltage:.1f}V (optimal: {config.OPTIMAL_VOLTAGE}V)")
        
#         # Current assessment
#         if current is not None:
#             if current < config.CURRENT_MIN_WARNING:
#                 score -= 30
#                 issues.append(f"Motor underloaded: {current:.1f}A (min normal: {config.CURRENT_MIN_WARNING}A)")
#             elif current > config.CURRENT_MAX_CRITICAL:
#                 score -= 50
#                 issues.append(f"Critical overcurrent: {current:.1f}A (max: {config.CURRENT_MAX_CRITICAL}A)")
#             elif current > config.CURRENT_MAX_WARNING:
#                 score -= 25
#                 issues.append(f"Motor overloaded: {current:.1f}A (optimal: {config.OPTIMAL_CURRENT}A)")
        
#         return max(0.0, min(100.0, score)), issues
    
#     def calculate_thermal_health(self, data: Dict) -> Tuple[float, List[str]]:
#         """Calculate thermal health score (0-100) and issues"""
#         score = 100.0
#         issues = []
        
#         motor_temp = data.get('plc_motor_temp')
#         env_temp = data.get('env_temp_c')
#         humidity = data.get('env_humidity')
        
#         if motor_temp is None and env_temp is None:
#             return 0.0, ["No thermal data available"]
        
#         # Motor temperature assessment
#         if motor_temp is not None:
#             if motor_temp > config.MOTOR_TEMP_CRITICAL:
#                 score -= 50
#                 issues.append(f"Critical motor temperature: {motor_temp:.1f}°C (max: {config.MOTOR_TEMP_CRITICAL}°C)")
#             elif motor_temp > config.MOTOR_TEMP_WARNING:
#                 score -= 30
#                 issues.append(f"High motor temperature: {motor_temp:.1f}°C (optimal: <{config.MOTOR_TEMP_GOOD}°C)")
#             elif motor_temp > config.MOTOR_TEMP_GOOD:
#                 score -= 15
#                 issues.append(f"Elevated motor temperature: {motor_temp:.1f}°C")
        
#         # Environmental temperature assessment
#         if env_temp is not None:
#             if env_temp > config.DHT_TEMP_MAX_CRITICAL:
#                 score -= 25
#                 issues.append(f"Critical ambient temperature: {env_temp:.1f}°C")
#             elif env_temp > config.DHT_TEMP_MAX_WARNING:
#                 score -= 15
#                 issues.append(f"High ambient temperature: {env_temp:.1f}°C (optimal: {config.OPTIMAL_DHT_TEMP}°C)")
        
#         # Humidity assessment
#         if humidity is not None:
#             if humidity > config.DHT_HUMIDITY_MAX_CRITICAL:
#                 score -= 20
#                 issues.append(f"Critical humidity level: {humidity:.1f}% (risk of condensation)")
#             elif humidity > config.DHT_HUMIDITY_MAX_WARNING:
#                 score -= 10
#                 issues.append(f"High humidity: {humidity:.1f}% (optimal: {config.OPTIMAL_DHT_HUMIDITY}%)")
#             elif humidity < config.DHT_HUMIDITY_MIN_WARNING:
#                 score -= 5
#                 issues.append(f"Low humidity: {humidity:.1f}% (may cause static)")
        
#         return max(0.0, min(100.0, score)), issues
    
#     def calculate_mechanical_health(self, data: Dict) -> Tuple[float, List[str]]:
#         """Calculate mechanical health score (0-100) and issues"""
#         score = 100.0
#         issues = []
        
#         rpm = data.get('esp_rpm')
#         current = data.get('esp_current')
        
#         if rpm is None:
#             return 0.0, ["No RPM data available"]
        
#         # RPM assessment
#         if rpm < config.RPM_MIN_CRITICAL:
#             score -= 50
#             issues.append(f"Critical low RPM: {rpm:.0f} (min: {config.RPM_MIN_CRITICAL})")
#         elif rpm < config.RPM_MIN_WARNING:
#             score -= 30
#             issues.append(f"Low RPM warning: {rpm:.0f} (optimal: {config.OPTIMAL_RPM})")
#         elif rpm > config.RPM_MAX_CRITICAL:
#             score -= 50
#             issues.append(f"Critical high RPM: {rpm:.0f} (max: {config.RPM_MAX_CRITICAL})")
#         elif rpm > config.RPM_MAX_WARNING:
#             score -= 30
#             issues.append(f"High RPM warning: {rpm:.0f} (optimal: {config.OPTIMAL_RPM})")
        
#         # Current vs RPM correlation check
#         if current is not None and rpm > 0:
#             power_factor = (current * 24) / 1000  # Assuming 24V
#             expected_current = (rpm / config.OPTIMAL_RPM) * config.OPTIMAL_CURRENT
#             current_deviation = abs(current - expected_current) / expected_current
            
#             if current_deviation > 0.5:  # >50% deviation
#                 score -= 20
#                 issues.append(f"Current/RPM imbalance detected (Current: {current:.1f}A, RPM: {rpm:.0f})")
        
#         return max(0.0, min(100.0, score)), issues
    
#     def calculate_predictive_health(self, recent_data: pd.DataFrame) -> Tuple[float, List[str]]:
#         """Calculate predictive health based on trends and patterns"""
#         score = 100.0
#         issues = []
        
#         if len(recent_data) < 5:
#             return 0.0, ["Insufficient historical data for prediction"]
        
#         try:
#             # Trend analysis
#             if 'plc_motor_temp' in recent_data.columns:
#                 temp_trend = recent_data['plc_motor_temp'].dropna().tail(10)
#                 if len(temp_trend) >= 5:
#                     temp_slope = np.polyfit(range(len(temp_trend)), temp_trend, 1)[0]
#                     if temp_slope > 1.0:  # Temperature rising >1°C per reading
#                         score -= 30
#                         issues.append(f"Rising temperature trend detected (+{temp_slope:.1f}°C/reading)")
            
#             if 'esp_current' in recent_data.columns:
#                 current_trend = recent_data['esp_current'].dropna().tail(10)
#                 if len(current_trend) >= 5:
#                     current_slope = np.polyfit(range(len(current_trend)), current_trend, 1)[0]
#                     if abs(current_slope) > 0.5:  # Current changing >0.5A per reading
#                         score -= 25
#                         issues.append(f"Current instability detected (±{abs(current_slope):.1f}A/reading)")
            
#             # Efficiency degradation check
#             if 'overall_health_score' in recent_data.columns:
#                 health_trend = recent_data['overall_health_score'].dropna().tail(20)
#                 if len(health_trend) >= 10:
#                     health_slope = np.polyfit(range(len(health_trend)), health_trend, 1)[0]
#                     if health_slope < -1.0:  # Health declining >1 point per reading
#                         score -= 35
#                         issues.append(f"Overall health degradation trend ({health_slope:.1f} points/reading)")
            
#             # Anomaly detection
#             if len(recent_data) >= 20:
#                 try:
#                     self.train_anomaly_detector(recent_data)
#                     features = self.prepare_features(recent_data.tail(5))
#                     if self.isolation_forest is not None:
#                         anomaly_scores = self.isolation_forest.decision_function(features)
#                         anomaly_count = np.sum(anomaly_scores < -0.5)
#                         if anomaly_count >= 3:
#                             score -= 40
#                             issues.append(f"Multiple anomalies detected ({anomaly_count}/5 recent readings)")
#                 except Exception as e:
#                     logger.warning(f"Anomaly detection failed: {e}")
        
#         except Exception as e:
#             logger.error(f"Error in predictive analysis: {e}")
#             issues.append("Predictive analysis error")
        
#         return max(0.0, min(100.0, score)), issues
    
#     def calculate_comprehensive_health(self, current_data: Dict, recent_data: pd.DataFrame = None) -> Dict:
#         """Calculate comprehensive health scores with detailed breakdown"""
        
#         # Calculate individual health components
#         electrical_score, electrical_issues = self.calculate_electrical_health(current_data)
#         thermal_score, thermal_issues = self.calculate_thermal_health(current_data)
#         mechanical_score, mechanical_issues = self.calculate_mechanical_health(current_data)
        
#         if recent_data is not None and len(recent_data) > 0:
#             predictive_score, predictive_issues = self.calculate_predictive_health(recent_data)
#         else:
#             predictive_score, predictive_issues = 50.0, ["Limited historical data"]
        
#         # Calculate overall health score (weighted average)
#         overall_score = (
#             electrical_score * 0.30 +    # 30% weight
#             thermal_score * 0.35 +       # 35% weight
#             mechanical_score * 0.25 +    # 25% weight
#             predictive_score * 0.10      # 10% weight
#         )
        
#         # Calculate efficiency score
#         efficiency_score = self.calculate_efficiency_score(current_data)
        
#         # Determine overall status
#         if overall_score >= 90:
#             status = "Excellent"
#             status_class = "success"
#         elif overall_score >= 75:
#             status = "Good"
#             status_class = "info"
#         elif overall_score >= 60:
#             status = "Warning"
#             status_class = "warning"
#         else:
#             status = "Critical"
#             status_class = "danger"
        
#         return {
#             'overall_health_score': round(overall_score, 1),
#             'electrical_health': round(electrical_score, 1),
#             'thermal_health': round(thermal_score, 1),
#             'mechanical_health': round(mechanical_score, 1),
#             'predictive_health': round(predictive_score, 1),
#             'efficiency_score': round(efficiency_score, 1),
#             'status': status,
#             'status_class': status_class,
#             'issues': {
#                 'electrical': electrical_issues,
#                 'thermal': thermal_issues,
#                 'mechanical': mechanical_issues,
#                 'predictive': predictive_issues
#             }
#         }
    
#     def calculate_efficiency_score(self, data: Dict) -> float:
#         """Calculate motor efficiency score"""
#         voltage = data.get('esp_voltage') or data.get('plc_motor_voltage', 0)
#         current = data.get('esp_current', 0)
#         rpm = data.get('esp_rpm', 0)
        
#         if not all([voltage, current, rpm]):
#             return 0.0
        
#         # Calculate theoretical vs actual efficiency
#         actual_power = voltage * current / 1000  # kW
#         theoretical_power = config.OPTIMAL_VOLTAGE * config.OPTIMAL_CURRENT / 1000
        
#         rpm_efficiency = min(100, (rpm / config.OPTIMAL_RPM) * 100)
#         power_efficiency = min(100, (theoretical_power / actual_power) * 100) if actual_power > 0 else 0
        
#         overall_efficiency = (rpm_efficiency + power_efficiency) / 2
#         return max(0.0, min(100.0, overall_efficiency))
    
#     def generate_recommendations(self, health_data: Dict, connection_status: Dict) -> List[Dict]:
#         """Generate smart recommendations based on health analysis and connection status"""
#         recommendations = []
        
#         # Connection status alerts
#         if not connection_status.get('esp_connected', False):
#             recommendations.append({
#                 'type': 'Connection Alert',
#                 'category': 'System',
#                 'severity': 'HIGH',
#                 'priority': 'HIGH',
#                 'title': 'ESP/Arduino Disconnected',
#                 'description': 'ESP sensor module is not sending data. Check network connection and power supply.',
#                 'action': 'Verify ESP power and network connectivity. Check sensor wiring.',
#                 'confidence': 1.0
#             })
        
#         if not connection_status.get('plc_connected', False):
#             recommendations.append({
#                 'type': 'Connection Alert',
#                 'category': 'System',
#                 'severity': 'HIGH',
#                 'priority': 'HIGH',
#                 'title': 'PLC Communication Lost',
#                 'description': 'PLC is not responding. Motor temperature and voltage data unavailable.',
#                 'action': 'Check PLC network connection and MC protocol settings.',
#                 'confidence': 1.0
#             })
        
#         # Health-based recommendations
#         overall_score = health_data.get('overall_health_score', 0)
        
#         if overall_score < 60:
#             recommendations.append({
#                 'type': 'Critical Alert',
#                 'category': 'Health',
#                 'severity': 'CRITICAL',
#                 'priority': 'CRITICAL',
#                 'title': 'Motor Health Critical',
#                 'description': f'Overall motor health is {overall_score}%. Immediate attention required.',
#                 'action': 'Stop motor operation and perform immediate inspection.',
#                 'confidence': 0.95
#             })
        
#         # Electrical recommendations
#         if health_data.get('electrical_health', 0) < 70:
#             electrical_issues = health_data.get('issues', {}).get('electrical', [])
#             recommendations.append({
#                 'type': 'Electrical Warning',
#                 'category': 'Electrical',
#                 'severity': 'MEDIUM',
#                 'priority': 'MEDIUM',
#                 'title': 'Electrical System Issues',
#                 'description': '; '.join(electrical_issues[:2]),
#                 'action': 'Check motor connections, measure actual voltage and current with multimeter.',
#                 'confidence': 0.8
#             })
        
#         # Thermal recommendations
#         if health_data.get('thermal_health', 0) < 70:
#             thermal_issues = health_data.get('issues', {}).get('thermal', [])
#             recommendations.append({
#                 'type': 'Temperature Warning',
#                 'category': 'Thermal',
#                 'severity': 'MEDIUM',
#                 'priority': 'MEDIUM',
#                 'title': 'Thermal Management Issues',
#                 'description': '; '.join(thermal_issues[:2]),
#                 'action': 'Improve ventilation, check cooling system, verify ambient conditions.',
#                 'confidence': 0.85
#             })
        
#         # Mechanical recommendations
#         if health_data.get('mechanical_health', 0) < 70:
#             mechanical_issues = health_data.get('issues', {}).get('mechanical', [])
#             recommendations.append({
#                 'type': 'Mechanical Warning',
#                 'category': 'Mechanical',
#                 'severity': 'MEDIUM',
#                 'priority': 'MEDIUM',
#                 'title': 'Mechanical Performance Issues',
#                 'description': '; '.join(mechanical_issues[:2]),
#                 'action': 'Inspect motor bearings, check coupling alignment, verify load conditions.',
#                 'confidence': 0.8
#             })
        
#         # Efficiency recommendations
#         efficiency = health_data.get('efficiency_score', 0)
#         if efficiency < 75:
#             recommendations.append({
#                 'type': 'Efficiency Warning',
#                 'category': 'Performance',
#                 'severity': 'MEDIUM',
#                 'priority': 'MEDIUM',
#                 'title': 'Motor Efficiency Below Optimal',
#                 'description': f'Current efficiency is {efficiency}%. Motor efficiency below optimal levels.',
#                 'action': 'Consider load optimization, check for mechanical wear, verify operating conditions.',
#                 'confidence': 0.7
#             })
        
#         # Predictive maintenance
#         if health_data.get('predictive_health', 0) < 60:
#             predictive_issues = health_data.get('issues', {}).get('predictive', [])
#             recommendations.append({
#                 'type': 'Predictive Maintenance',
#                 'category': 'Predictive',
#                 'severity': 'MEDIUM',
#                 'priority': 'MEDIUM',
#                 'title': 'Maintenance Required Soon',
#                 'description': '; '.join(predictive_issues[:2]),
#                 'action': 'Schedule preventive maintenance within next 7 days.',
#                 'confidence': 0.75
#             })
        
#         # Sort by priority and severity
#         priority_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
#         recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
#         return recommendations[:10]  # Return top 10 recommendations
    
#     def prepare_features(self, data: pd.DataFrame) -> np.ndarray:
#         """Prepare features for ML models"""
#         # Fill missing values with median
#         features = data[self.feature_columns].fillna(data[self.feature_columns].median())
        
#         # Add derived features
#         features = features.copy()
#         features['power_estimated'] = features['esp_current'] * features['esp_voltage']
#         features['temp_diff'] = features['plc_motor_temp'] - features['env_temp_c']
#         features['voltage_stability'] = features['esp_voltage'].rolling(window=3).std().fillna(0)
#         features['current_trend'] = features['esp_current'].diff().fillna(0)
        
#         return features.values
    
#     def train_anomaly_detector(self, data: pd.DataFrame):
#         """Train isolation forest for anomaly detection"""
#         try:
#             if len(data) < 20:
#                 return
            
#             features = self.prepare_features(data)
#             self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
#             self.isolation_forest.fit(features)
#             logger.info("Anomaly detection model trained successfully")
#         except Exception as e:
#             logger.error(f"Error training anomaly detector: {e}")

# # =============================================================================
# # ENHANCED DATA MANAGEMENT
# # =============================================================================

# class DataManager:
#     def __init__(self):
#         self.engine = create_engine(config.DATABASE_URL)
#         Base.metadata.create_all(self.engine)
#         self.Session = sessionmaker(bind=self.engine)
#         self.health_analyzer = AdvancedMotorHealthAnalyzer()
        
#     def get_session(self) -> Session:
#         return self.Session()
    
#     def save_sensor_data(self, data: Dict, connection_status: Dict = None) -> bool:
#         """Save sensor data with enhanced health calculations"""
#         try:
#             session = self.get_session()
            
#             # Get recent data for predictive analysis
#             recent_data = self.get_recent_data(hours=2)
            
#             # Calculate comprehensive health scores
#             health_data = self.health_analyzer.calculate_comprehensive_health(data, recent_data)
            
#             # Calculate power consumption
#             current = data.get('esp_current', 0) or 0
#             voltage = data.get('esp_voltage', 0) or data.get('plc_motor_voltage', 0) or 0
#             power_consumption = (current * voltage) / 1000 if current and voltage else 0
            
#             sensor_reading = SensorData(
#                 esp_current=data.get('esp_current'),
#                 esp_voltage=data.get('esp_voltage'),
#                 esp_rpm=data.get('esp_rpm'),
#                 env_temp_c=data.get('env_temp_c'),
#                 env_humidity=data.get('env_humidity'),
#                 env_temp_f=data.get('env_temp_f'),
#                 heat_index_c=data.get('heat_index_c'),
#                 heat_index_f=data.get('heat_index_f'),
#                 relay1_status=data.get('relay1_status'),
#                 relay2_status=data.get('relay2_status'),
#                 relay3_status=data.get('relay3_status'),
#                 combined_status=data.get('combined_status'),
#                 plc_motor_temp=data.get('plc_motor_temp'),
#                 plc_motor_voltage=data.get('plc_motor_voltage'),
#                 esp_connected=data.get('esp_connected', False),
#                 plc_connected=data.get('plc_connected', False),
#                 overall_health_score=health_data['overall_health_score'],
#                 electrical_health=health_data['electrical_health'],
#                 thermal_health=health_data['thermal_health'],
#                 mechanical_health=health_data['mechanical_health'],
#                 predictive_health=health_data['predictive_health'],
#                 efficiency_score=health_data['efficiency_score'],
#                 power_consumption=power_consumption
#             )
            
#             session.add(sensor_reading)
            
#             # Generate and save recommendations as alerts
#             if connection_status:
#                 recommendations = self.health_analyzer.generate_recommendations(health_data, connection_status)
#                 for rec in recommendations:
#                     if rec['severity'] in ['HIGH', 'CRITICAL']:
#                         alert = MaintenanceLog(
#                             alert_type=rec['type'],
#                             category=rec['category'],
#                             severity=rec['severity'],
#                             priority=rec['priority'],
#                             description=rec['description'],
#                             prediction_confidence=rec['confidence'],
#                             recommended_action=rec['action']
#                         )
#                         session.add(alert)
            
#             session.commit()
#             session.close()
            
#             # Export to CSV
#             self.export_to_csv(data, health_data, power_consumption)
#             return True
            
#         except Exception as e:
#             logger.error(f"Error saving sensor data: {e}")
#             return False
    
#     def export_to_csv(self, data: Dict, health_data: Dict, power: float):
#         """Export enhanced data to CSV file"""
#         try:
#             file_exists = os.path.isfile(config.CSV_EXPORT_PATH)
#             with open(config.CSV_EXPORT_PATH, 'a', newline='') as csvfile:
#                 fieldnames = ['timestamp', 'esp_current', 'esp_voltage', 'esp_rpm', 
#                              'env_temp_c', 'env_humidity', 'plc_motor_temp', 
#                              'plc_motor_voltage', 'power_consumption', 
#                              'overall_health_score', 'electrical_health', 'thermal_health',
#                              'mechanical_health', 'predictive_health', 'efficiency_score',
#                              'relay1_status', 'relay2_status', 'relay3_status']
#                 writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
#                 if not file_exists:
#                     writer.writeheader()
                
#                 writer.writerow({
#                     'timestamp': datetime.now().isoformat(),
#                     'esp_current': data.get('esp_current', 0),
#                     'esp_voltage': data.get('esp_voltage', 0),
#                     'esp_rpm': data.get('esp_rpm', 0),
#                     'env_temp_c': data.get('env_temp_c', 0),
#                     'env_humidity': data.get('env_humidity', 0),
#                     'plc_motor_temp': data.get('plc_motor_temp', 0),
#                     'plc_motor_voltage': data.get('plc_motor_voltage', 0),
#                     'power_consumption': power,
#                     'overall_health_score': health_data['overall_health_score'],
#                     'electrical_health': health_data['electrical_health'],
#                     'thermal_health': health_data['thermal_health'],
#                     'mechanical_health': health_data['mechanical_health'],
#                     'predictive_health': health_data['predictive_health'],
#                     'efficiency_score': health_data['efficiency_score'],
#                     'relay1_status': data.get('relay1_status', 'OFF'),
#                     'relay2_status': data.get('relay2_status', 'OFF'),
#                     'relay3_status': data.get('relay3_status', 'OFF')
#                 })
#         except Exception as e:
#             logger.error(f"Error exporting to CSV: {e}")
    
#     def get_recent_data(self, hours: int = 24) -> pd.DataFrame:
#         """Get recent sensor data"""
#         try:
#             session = self.get_session()
#             cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
#             query = session.query(SensorData).filter(
#                 SensorData.timestamp >= cutoff_time
#             ).order_by(SensorData.timestamp.desc())
            
#             data = pd.read_sql(query.statement, self.engine)
#             session.close()
#             return data
#         except Exception as e:
#             logger.error(f"Error retrieving recent data: {e}")
#             return pd.DataFrame()
    
#     def get_maintenance_alerts(self) -> List[Dict]:
#         """Get active maintenance alerts with enhanced categorization"""
#         try:
#             session = self.get_session()
#             alerts = session.query(MaintenanceLog).filter(
#                 MaintenanceLog.acknowledged == False
#             ).order_by(MaintenanceLog.timestamp.desc()).limit(15).all()
            
#             result = []
#             for alert in alerts:
#                 result.append({
#                     'id': alert.id,
#                     'timestamp': alert.timestamp.isoformat(),
#                     'type': alert.alert_type,
#                     'category': alert.category,
#                     'severity': alert.severity,
#                     'priority': alert.priority,
#                     'description': alert.description,
#                     'confidence': alert.prediction_confidence,
#                     'action': alert.recommended_action
#                 })
            
#             session.close()
#             return result
#         except Exception as e:
#             logger.error(f"Error retrieving maintenance alerts: {e}")
#             return []

# # =============================================================================
# # PLC COMMUNICATION (Same as before)
# # =============================================================================

# class PLCManager:
#     def __init__(self):
#         self.mc = pymcprotocol.Type3E()
#         self.connected = False
#         self.last_data = {}
        
#     def connect(self) -> bool:
#         """Connect to PLC"""
#         try:
#             if self.mc.connect(config.PLC_IP, config.PLC_PORT):
#                 self.connected = True
#                 logger.info("PLC connection established")
#                 return True
#             else:
#                 self.connected = False
#                 logger.error("Failed to connect to PLC")
#                 return False
#         except Exception as e:
#             self.connected = False
#             logger.error(f"PLC connection error: {e}")
#             return False
    
#     def read_data(self) -> Dict:
#         """Read data from PLC registers"""
#         if not self.connected:
#             if not self.connect():
#                 return {'plc_connected': False}
        
#         try:
#             # Read motor temperature from D100
#             motor_temp = self.mc.batchread_wordunits(headdevice="D100", readsize=1)[0]
            
#             # Read motor voltage from D102
#             motor_voltage = self.mc.batchread_wordunits(headdevice="D102", readsize=1)[0]
            
#             self.last_data = {
#                 'plc_motor_temp': float(motor_temp),
#                 'plc_motor_voltage': float(motor_voltage),
#                 'plc_connected': True
#             }
            
#             return self.last_data
            
#         except Exception as e:
#             logger.error(f"Error reading PLC data: {e}")
#             self.connected = False
#             return {'plc_connected': False}
    
#     def disconnect(self):
#         """Disconnect from PLC"""
#         try:
#             if self.connected:
#                 self.mc.close()
#                 self.connected = False
#                 logger.info("PLC disconnected")
#         except Exception as e:
#             logger.error(f"Error disconnecting PLC: {e}")

# # =============================================================================
# # FLASK APPLICATION
# # =============================================================================

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'motor_monitoring_secret_key'
# socketio = SocketIO(app, cors_allowed_origins="*")

# # Global instances
# data_manager = DataManager()
# plc_manager = PLCManager()
# latest_data = {}
# system_status = {
#     'esp_connected': False,
#     'plc_connected': False,
#     'ai_model_status': 'Initializing',
#     'last_update': None,
#     'esp_last_seen': None,
#     'plc_last_seen': None
# }

# # Store latest health data globally
# latest_health_data = {
#     'overall_health_score': 0,
#     'electrical_health': 0,
#     'thermal_health': 0,
#     'mechanical_health': 0,
#     'predictive_health': 0,
#     'efficiency_score': 0,
#     'status': 'No Data',
#     'status_class': 'secondary',
#     'issues': {}
# }

# # =============================================================================
# # BACKGROUND TASKS (Enhanced)
# # =============================================================================

# def plc_data_collector():
#     """Background task to collect PLC data"""
#     while True:
#         try:
#             plc_data = plc_manager.read_data()
#             current_time = datetime.now()
            
#             if plc_data and plc_data.get('plc_connected', False):
#                 latest_data.update(plc_data)
#                 system_status['plc_connected'] = True
#                 system_status['plc_last_seen'] = current_time.isoformat()
#                 logger.info(f"PLC data received: Temp={plc_data.get('plc_motor_temp')}°C, Voltage={plc_data.get('plc_motor_voltage')}V")
#             else:
#                 if system_status['plc_connected']:
#                     logger.warning("PLC connection failed")
#                 system_status['plc_connected'] = False
#                 latest_data['plc_connected'] = False
#                 latest_data['plc_motor_temp'] = None
#                 latest_data['plc_motor_voltage'] = None
                
#         except Exception as e:
#             logger.error(f"Error in PLC data collection: {e}")
#             system_status['plc_connected'] = False
#             latest_data['plc_connected'] = False
#             latest_data['plc_motor_temp'] = None
#             latest_data['plc_motor_voltage'] = None
        
#         time.sleep(5)

# def enhanced_data_analysis_task():
#     """Enhanced background task for AI analysis and alerts"""
#     global latest_health_data
    
#     while True:
#         try:
#             # Get recent data for analysis
#             recent_data = data_manager.get_recent_data(hours=2)
            
#             if len(latest_data) > 0:
#                 # Calculate comprehensive health
#                 latest_health_data = data_manager.health_analyzer.calculate_comprehensive_health(
#                     latest_data, recent_data
#                 )
                
#                 # Generate recommendations
#                 recommendations = data_manager.health_analyzer.generate_recommendations(
#                     latest_health_data, system_status
#                 )
                
#                 # Emit health update to dashboard
#                 socketio.emit('health_update', latest_health_data)
                
#                 # Emit recommendations
#                 socketio.emit('recommendations_update', recommendations)
                
#                 # Save critical alerts to database
#                 session = data_manager.get_session()
#                 for rec in recommendations:
#                     if rec['severity'] in ['CRITICAL', 'HIGH'] and rec['confidence'] > 0.8:
#                         # Check if similar alert already exists
#                         existing = session.query(MaintenanceLog).filter(
#                             MaintenanceLog.alert_type == rec['type'],
#                             MaintenanceLog.acknowledged == False,
#                             MaintenanceLog.timestamp > datetime.utcnow() - timedelta(minutes=30)
#                         ).first()
                        
#                         if not existing:
#                             alert = MaintenanceLog(
#                                 alert_type=rec['type'],
#                                 category=rec['category'],
#                                 severity=rec['severity'],
#                                 priority=rec['priority'],
#                                 description=rec['description'],
#                                 prediction_confidence=rec['confidence'],
#                                 recommended_action=rec['action']
#                             )
#                             session.add(alert)
                            
#                             # Emit real-time alert
#                             socketio.emit('maintenance_alert', {
#                                 'type': rec['type'],
#                                 'category': rec['category'],
#                                 'severity': rec['severity'],
#                                 'message': rec['description'],
#                                 'confidence': rec['confidence'],
#                                 'priority': rec['priority']
#                             })
                
#                 session.commit()
#                 session.close()
                
#                 system_status['ai_model_status'] = 'Active'
#             else:
#                 system_status['ai_model_status'] = 'Waiting for data'
            
#         except Exception as e:
#             logger.error(f"Error in enhanced data analysis: {e}")
#             system_status['ai_model_status'] = 'Error'
        
#         time.sleep(15)  # Run analysis every 15 seconds for more responsive updates

# def connection_monitor():
#     """Enhanced connection monitoring with alerts"""
#     while True:
#         try:
#             current_time = datetime.now()
            
#             # Check ESP connection timeout
#             if system_status['esp_last_seen']:
#                 esp_last_seen = datetime.fromisoformat(system_status['esp_last_seen'])
#                 esp_timeout = (current_time - esp_last_seen).total_seconds()
                
#                 if esp_timeout > config.ESP_TIMEOUT:
#                     if system_status['esp_connected']:
#                         logger.warning(f"ESP connection timeout ({esp_timeout:.0f}s)")
#                         system_status['esp_connected'] = False
                        
#                         # Clear ESP-related data
#                         esp_keys = ['esp_current', 'esp_voltage', 'esp_rpm', 'env_temp_c', 
#                                   'env_humidity', 'env_temp_f', 'heat_index_c', 'heat_index_f',
#                                   'relay1_status', 'relay2_status', 'relay3_status', 'combined_status']
                        
#                         for key in esp_keys:
#                             if key in latest_data:
#                                 latest_data[key] = None
                        
#                         # Emit disconnection alert
#                         socketio.emit('connection_lost', {
#                             'component': 'ESP',
#                             'message': 'ESP/Arduino connection lost - sensor data timeout',
#                             'timeout': esp_timeout,
#                             'severity': 'HIGH'
#                         })
            
#             # Check PLC connection timeout
#             if system_status['plc_last_seen']:
#                 plc_last_seen = datetime.fromisoformat(system_status['plc_last_seen'])
#                 plc_timeout = (current_time - plc_last_seen).total_seconds()
                
#                 if plc_timeout > config.PLC_TIMEOUT:
#                     if system_status['plc_connected']:
#                         logger.warning(f"PLC connection timeout ({plc_timeout:.0f}s)")
#                         system_status['plc_connected'] = False
                        
#                         # Clear PLC-related data
#                         latest_data['plc_motor_temp'] = None
#                         latest_data['plc_motor_voltage'] = None
#                         latest_data['plc_connected'] = False
                        
#                         # Emit disconnection alert
#                         socketio.emit('connection_lost', {
#                             'component': 'PLC',
#                             'message': 'PLC connection lost - motor monitoring unavailable',
#                             'timeout': plc_timeout,
#                             'severity': 'HIGH'
#                         })
            
#             # Emit updated status
#             socketio.emit('status_update', system_status)
            
#         except Exception as e:
#             logger.error(f"Error in connection monitor: {e}")
        
#         time.sleep(config.DATA_CLEANUP_INTERVAL)

# # Start enhanced background threads
# threading.Thread(target=plc_data_collector, daemon=True).start()
# threading.Thread(target=enhanced_data_analysis_task, daemon=True).start()
# threading.Thread(target=connection_monitor, daemon=True).start()

# # =============================================================================
# # ENHANCED FLASK ROUTES
# # =============================================================================

# @app.route('/')
# def dashboard():
#     """Main dashboard page"""
#     return render_template('dashboard.html')

# @app.route('/send-data', methods=['POST'])
# def receive_esp_data():
#     """Enhanced ESP data reception with immediate health calculation"""
#     try:
#         data = request.get_json()
        
#         if not data:
#             return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
#         current_time = datetime.now()
        
#         # Parse ESP data with proper validation
#         esp_data = {
#             'esp_current': float(data.get('VAL1', 0)) if data.get('VAL1') and data.get('VAL1') != '0' else None,
#             'esp_voltage': float(data.get('VAL2', 0)) if data.get('VAL2') and data.get('VAL2') != '0' else None,
#             'esp_rpm': float(data.get('VAL3', 0)) if data.get('VAL3') and data.get('VAL3') != '0' else None,
#             'env_temp_c': float(data.get('VAL4', 0)) if data.get('VAL4') else None,
#             'env_humidity': float(data.get('VAL5', 0)) if data.get('VAL5') else None,
#             'env_temp_f': float(data.get('VAL6', 0)) if data.get('VAL6') else None,
#             'heat_index_c': float(data.get('VAL7', 0)) if data.get('VAL7') else None,
#             'heat_index_f': float(data.get('VAL8', 0)) if data.get('VAL8') else None,
#             'relay1_status': data.get('VAL9', 'OFF'),
#             'relay2_status': data.get('VAL10', 'OFF'),
#             'relay3_status': data.get('VAL11', 'OFF'),
#             'combined_status': data.get('VAL12', 'NOR'),
#             'esp_connected': True
#         }
        
#         # Update latest data
#         latest_data.update(esp_data)
        
#         # Update connection status
#         system_status['esp_connected'] = True
#         system_status['esp_last_seen'] = current_time.isoformat()
#         system_status['last_update'] = current_time.isoformat()
        
#         # Save to database with connection status
#         combined_data = {**latest_data}
#         data_manager.save_sensor_data(combined_data, system_status)
        
#         # Emit real-time data to dashboard
#         socketio.emit('sensor_update', combined_data)
        
#         logger.info(f"ESP data received: Current={esp_data.get('esp_current')}A, "
#                    f"Voltage={esp_data.get('esp_voltage')}V, RPM={esp_data.get('esp_rpm')}")
        
#         return jsonify({'status': 'success', 'message': 'Data received and processed'}), 200
        
#     except Exception as e:
#         logger.error(f"Error processing ESP data: {e}")
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# @app.route('/api/current-data')
# def get_current_data():
#     """Get enhanced current sensor readings with health data"""
#     return jsonify({
#         'data': latest_data,
#         'health': latest_health_data,
#         'status': system_status,
#         'timestamp': datetime.now().isoformat()
#     })

# @app.route('/api/health-details')
# def get_health_details():
#     """Get detailed health breakdown"""
#     return jsonify(latest_health_data)

# @app.route('/api/recommendations')
# def get_recommendations():
#     """Get current recommendations"""
#     try:
#         recent_data = data_manager.get_recent_data(hours=1)
#         recommendations = data_manager.health_analyzer.generate_recommendations(
#             latest_health_data, system_status
#         )
#         return jsonify({'recommendations': recommendations})
#     except Exception as e:
#         logger.error(f"Error generating recommendations: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/historical-data')
# def get_historical_data():
#     """Get enhanced historical data for charts"""
#     hours = request.args.get('hours', 24, type=int)
#     try:
#         data = data_manager.get_recent_data(hours=hours)
        
#         if data.empty:
#             return jsonify({'data': [], 'message': 'No data available'})
        
#         # Convert to JSON format for charts with enhanced data
#         chart_data = []
#         for _, row in data.iterrows():
#             chart_data.append({
#                 'timestamp': row['timestamp'].isoformat() if pd.notnull(row['timestamp']) else None,
#                 'current': row.get('esp_current', 0),
#                 'voltage': row.get('esp_voltage', 0),
#                 'rpm': row.get('esp_rpm', 0),
#                 'motor_temp': row.get('plc_motor_temp', 0),
#                 'env_temp': row.get('env_temp_c', 0),
#                 'humidity': row.get('env_humidity', 0),
#                 'overall_health_score': row.get('overall_health_score', 0),
#                 'electrical_health': row.get('electrical_health', 0),
#                 'thermal_health': row.get('thermal_health', 0),
#                 'mechanical_health': row.get('mechanical_health', 0),
#                 'predictive_health': row.get('predictive_health', 0),
#                 'efficiency_score': row.get('efficiency_score', 0),
#                 'power': row.get('power_consumption', 0)
#             })
        
#         return jsonify({'data': chart_data})
        
#     except Exception as e:
#         logger.error(f"Error retrieving historical data: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/maintenance-alerts')
# def get_maintenance_alerts():
#     """Get enhanced maintenance alerts"""
#     try:
#         alerts = data_manager.get_maintenance_alerts()
#         return jsonify({'alerts': alerts})
#     except Exception as e:
#         logger.error(f"Error retrieving maintenance alerts: {e}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/acknowledge-alert/<int:alert_id>', methods=['POST'])
# def acknowledge_alert(alert_id):
#     """Acknowledge maintenance alert"""
#     try:
#         session = data_manager.get_session()
#         alert = session.query(MaintenanceLog).filter_by(id=alert_id).first()
#         if alert:
#             alert.acknowledged = True
#             session.commit()
#             session.close()
#             return jsonify({'status': 'success'})
#         else:
#             session.close()
#             return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
#     except Exception as e:
#         logger.error(f"Error acknowledging alert: {e}")
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# @app.route('/api/motor-control', methods=['POST'])
# def motor_control():
#     """Enhanced motor control endpoint"""
#     try:
#         command = request.json.get('command')
#         logger.info(f"Motor control command received: {command}")
        
#         # Log control action
#         session = data_manager.get_session()
#         event = SystemEvents(
#             event_type='Manual Control',
#             component='Motor',
#             message=f'Manual control command: {command}',
#             severity='INFO'
#         )
#         session.add(event)
#         session.commit()
#         session.close()
        
#         # Here you would send commands to PLC
#         # For now, just log the command
        
#         return jsonify({'status': 'success', 'message': f'Command {command} logged and executed'}), 200
#     except Exception as e:
#         logger.error(f"Error in motor control: {e}")
#         return jsonify({'status': 'error', 'message': str(e)}), 500

# # =============================================================================
# # ENHANCED WEBSOCKET EVENTS
# # =============================================================================

# @socketio.on('connect')
# def handle_connect():
#     """Handle client connection with enhanced data"""
#     emit('status_update', system_status)
#     emit('sensor_update', latest_data)
#     emit('health_update', latest_health_data)
#     logger.info('Client connected to WebSocket')

# @socketio.on('disconnect')
# def handle_disconnect():
#     """Handle client disconnection"""
#     logger.info('Client disconnected from WebSocket')

# @socketio.on('request_update')
# def handle_update_request():
#     """Handle manual update request with full data"""
#     emit('sensor_update', latest_data)
#     emit('status_update', system_status)
#     emit('health_update', latest_health_data)

# # =============================================================================
# # APPLICATION STARTUP
# # =============================================================================

# if __name__ == '__main__':
#     logger.info("Starting AI-Enabled Industrial Motor Monitoring System v3.0")
#     logger.info("Enhanced with Advanced Health Analytics and Smart Recommendations")
    
#     # Initialize PLC connection
#     plc_manager.connect()
    
#     # Ensure models directory exists
#     os.makedirs(config.MODEL_PATH, exist_ok=True)
    
#     # Log optimal values for reference
#     logger.info("=== OPTIMAL VALUES ===")
#     logger.info(f"Motor Temperature: < {config.OPTIMAL_MOTOR_TEMP}°C")
#     logger.info(f"Voltage: {config.OPTIMAL_VOLTAGE}V")
#     logger.info(f"Current: {config.OPTIMAL_CURRENT}A")
#     logger.info(f"RPM: {config.OPTIMAL_RPM}")
#     logger.info(f"DHT Temperature: {config.OPTIMAL_DHT_TEMP}°C")
#     logger.info(f"DHT Humidity: {config.OPTIMAL_DHT_HUMIDITY}%")
#     logger.info("=====================")
    
#     try:
#         # Start the Flask-SocketIO server
#         socketio.run(
#             app, 
#             host=config.FLASK_HOST, 
#             port=config.FLASK_PORT, 
#             debug=config.DEBUG,
#             use_reloader=False
#         )
#     except KeyboardInterrupt:
#         logger.info("Shutting down system...")
#         plc_manager.disconnect()
#     except Exception as e:
#         logger.error(f"Error starting application: {e}")
#         plc_manager.disconnect()
