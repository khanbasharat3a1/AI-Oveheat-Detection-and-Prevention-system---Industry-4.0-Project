"""
Motor Health Analyzer
AI-powered health analysis and recommendations
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class HealthAnalyzer:
    def __init__(self, config):
        self.config = config
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'esp_current', 'esp_voltage', 'esp_rpm', 'env_temp_c', 
            'env_humidity', 'plc_motor_temp', 'plc_motor_voltage'
        ]
        logger.info("Health Analyzer initialized")
    
    def calculate_electrical_health(self, data: Dict) -> Tuple[float, List[str]]:
        """Calculate electrical health score (0-100) and identify issues"""
        score = 100.0
        issues = []
        
        voltage = data.get('esp_voltage') or data.get('plc_motor_voltage')
        current = data.get('esp_current')
        
        if voltage is None and current is None:
            return 0.0, ["No electrical data available"]
        
        # Voltage assessment
        if voltage is not None:
            if voltage < self.config.VOLTAGE_MIN_CRITICAL:
                score -= 40
                issues.append(f"Critical undervoltage: {voltage:.1f}V")
            elif voltage < self.config.VOLTAGE_MIN_WARNING:
                score -= 20
                issues.append(f"Low voltage: {voltage:.1f}V")
            elif voltage > self.config.VOLTAGE_MAX_CRITICAL:
                score -= 40
                issues.append(f"Critical overvoltage: {voltage:.1f}V")
            elif voltage > self.config.VOLTAGE_MAX_WARNING:
                score -= 20
                issues.append(f"High voltage: {voltage:.1f}V")
        
        # Current assessment
        if current is not None:
            if current < self.config.CURRENT_MIN_WARNING:
                score -= 30
                issues.append(f"Motor underloaded: {current:.1f}A")
            elif current > self.config.CURRENT_MAX_CRITICAL:
                score -= 50
                issues.append(f"Critical overcurrent: {current:.1f}A")
            elif current > self.config.CURRENT_MAX_WARNING:
                score -= 25
                issues.append(f"Motor overloaded: {current:.1f}A")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_thermal_health(self, data: Dict) -> Tuple[float, List[str]]:
        """Calculate thermal health score (0-100) and identify issues"""
        score = 100.0
        issues = []
        
        motor_temp = data.get('plc_motor_temp')
        env_temp = data.get('env_temp_c')
        humidity = data.get('env_humidity')
        
        if motor_temp is None and env_temp is None:
            return 0.0, ["No thermal data available"]
        
        # Motor temperature assessment
        if motor_temp is not None:
            if motor_temp > self.config.MOTOR_TEMP_CRITICAL:
                score -= 50
                issues.append(f"Critical motor temperature: {motor_temp:.1f}°C")
            elif motor_temp > self.config.MOTOR_TEMP_WARNING:
                score -= 30
                issues.append(f"High motor temperature: {motor_temp:.1f}°C")
            elif motor_temp > self.config.MOTOR_TEMP_GOOD:
                score -= 15
                issues.append(f"Elevated motor temperature: {motor_temp:.1f}°C")
        
        # Environmental assessment
        if env_temp is not None:
            if env_temp > self.config.DHT_TEMP_MAX_CRITICAL:
                score -= 25
                issues.append(f"Critical ambient temperature: {env_temp:.1f}°C")
            elif env_temp > self.config.DHT_TEMP_MAX_WARNING:
                score -= 15
                issues.append(f"High ambient temperature: {env_temp:.1f}°C")
        
        if humidity is not None:
            if humidity > self.config.DHT_HUMIDITY_MAX_CRITICAL:
                score -= 20
                issues.append(f"Critical humidity: {humidity:.1f}%")
            elif humidity > self.config.DHT_HUMIDITY_MAX_WARNING:
                score -= 10
                issues.append(f"High humidity: {humidity:.1f}%")
            elif humidity < self.config.DHT_HUMIDITY_MIN_WARNING:
                score -= 5
                issues.append(f"Low humidity: {humidity:.1f}%")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_mechanical_health(self, data: Dict) -> Tuple[float, List[str]]:
        """Calculate mechanical health score (0-100) and identify issues"""
        score = 100.0
        issues = []
        
        rpm = data.get('esp_rpm')
        current = data.get('esp_current')
        
        if rpm is None:
            return 0.0, ["No RPM data available"]
        
        # RPM assessment
        if rpm < self.config.RPM_MIN_CRITICAL:
            score -= 50
            issues.append(f"Critical low RPM: {rpm:.0f}")
        elif rpm < self.config.RPM_MIN_WARNING:
            score -= 30
            issues.append(f"Low RPM: {rpm:.0f}")
        elif rpm > self.config.RPM_MAX_CRITICAL:
            score -= 50
            issues.append(f"Critical high RPM: {rpm:.0f}")
        elif rpm > self.config.RPM_MAX_WARNING:
            score -= 30
            issues.append(f"High RPM: {rpm:.0f}")
        
        # Load balance check
        if current is not None and rpm > 0:
            expected_current = (rpm / self.config.OPTIMAL_RPM) * self.config.OPTIMAL_CURRENT
            if expected_current > 0:
                current_deviation = abs(current - expected_current) / expected_current
                if current_deviation > 0.5:
                    score -= 20
                    issues.append(f"Current/RPM imbalance detected")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_predictive_health(self, recent_data: pd.DataFrame) -> Tuple[float, List[str]]:
        """Calculate predictive health based on trends"""
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
                        issues.append(f"Health degradation: {health_slope:.1f} points/reading")
        
        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
            issues.append("Predictive analysis error")
        
        return max(0.0, min(100.0, score)), issues
    
    def calculate_comprehensive_health(self, current_data: Dict, recent_data: pd.DataFrame = None) -> Dict:
        """Calculate comprehensive health scores with detailed breakdown"""
        
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
        """Calculate motor efficiency score"""
        voltage = data.get('esp_voltage') or data.get('plc_motor_voltage', 0)
        current = data.get('esp_current', 0)
        rpm = data.get('esp_rpm', 0)
        
        if not all([voltage, current, rpm]):
            return 0.0
        
        # Calculate efficiency metrics
        rpm_efficiency = min(100, (rpm / self.config.OPTIMAL_RPM) * 100)
        
        actual_power = voltage * current / 1000
        theoretical_power = self.config.OPTIMAL_VOLTAGE * self.config.OPTIMAL_CURRENT / 1000
        power_efficiency = min(100, (theoretical_power / actual_power) * 100) if actual_power > 0 else 0
        
        overall_efficiency = (rpm_efficiency + power_efficiency) / 2
        return max(0.0, min(100.0, overall_efficiency))
    
    def generate_recommendations(self, health_data: Dict, connection_status: Dict) -> List[Dict]:
        """Generate AI-powered recommendations"""
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
