"""
API Routes
All REST API endpoints and WebSocket event handlers
"""

import logging
from datetime import datetime
from flask import request, jsonify, render_template
from flask_socketio import emit

logger = logging.getLogger(__name__)

def setup_routes(app, system_instance):
    """Setup all Flask routes"""
    
    @app.route('/')
    def dashboard():
        """Main dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/send-data', methods=['POST'])
    def receive_esp_data():
        """Receive data from ESP/Arduino"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No data received'}), 400
            
            # Process ESP data
            result = system_instance.esp_handler.process_esp_data(system_instance, data)
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"Error in ESP data endpoint: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/current-data')
    def get_current_data():
        """Get current sensor readings with health data"""
        return jsonify({
            'data': system_instance.latest_data,
            'health': system_instance.latest_health_data,
            'status': system_instance.system_status,
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/health-details')
    def get_health_details():
        """Get detailed health breakdown"""
        return jsonify(system_instance.latest_health_data)
    
    @app.route('/api/recommendations')
    def get_recommendations():
        """Get current AI recommendations"""
        try:
            recent_data = system_instance.db_manager.get_recent_data(hours=1)
            recommendations = system_instance.health_analyzer.generate_recommendations(
                system_instance.latest_health_data, system_instance.system_status
            )
            return jsonify({'recommendations': recommendations})
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/historical-data')
    def get_historical_data():
        """Get historical data for charts"""
        hours = request.args.get('hours', 24, type=int)
        try:
            data = system_instance.db_manager.get_recent_data(hours=hours)
            
            if data.empty:
                return jsonify({'data': [], 'message': 'No data available'})
            
            # Convert to JSON format for charts
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
        """Get maintenance alerts"""
        try:
            alerts = system_instance.db_manager.get_maintenance_alerts()
            return jsonify({'alerts': alerts})
        except Exception as e:
            logger.error(f"Error retrieving alerts: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/acknowledge-alert/<int:alert_id>', methods=['POST'])
    def acknowledge_alert(alert_id):
        """Acknowledge maintenance alert"""
        try:
            success = system_instance.db_manager.acknowledge_alert(alert_id)
            if success:
                return jsonify({'status': 'success'})
            else:
                return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/motor-control', methods=['POST'])
    def motor_control():
        """Motor control endpoint"""
        try:
            command = request.json.get('command')
            logger.info(f"Motor control command: {command}")
            
            # Log control action
            system_instance.db_manager.log_system_event(
                'Manual Control', 'Motor', f'Command: {command}', 'INFO'
            )
            
            return jsonify({'status': 'success', 'message': f'Command {command} executed'}), 200
        except Exception as e:
            logger.error(f"Error in motor control: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/system-status')
    def get_system_status():
        """Get complete system status"""
        return jsonify({
            'system_status': system_instance.system_status,
            'esp_status': system_instance.esp_handler.get_esp_status(system_instance),
            'plc_status': system_instance.plc_manager.get_connection_status(),
            'health_summary': system_instance.latest_health_data
        })

def setup_websocket_events(socketio, system_instance):
    """Setup WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        emit('status_update', system_instance.system_status)
        emit('sensor_update', system_instance.latest_data)
        emit('health_update', system_instance.latest_health_data)
        logger.info('Client connected to WebSocket')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info('Client disconnected from WebSocket')
    
    @socketio.on('request_update')
    def handle_update_request():
        """Handle manual update request"""
        emit('sensor_update', system_instance.latest_data)
        emit('status_update', system_instance.system_status)
        emit('health_update', system_instance.latest_health_data)
    
    @socketio.on('request_recommendations')
    def handle_recommendations_request():
        """Handle recommendations request"""
        try:
            recommendations = system_instance.health_analyzer.generate_recommendations(
                system_instance.latest_health_data, system_instance.system_status
            )
            emit('recommendations_update', recommendations)
        except Exception as e:
            logger.error(f"Error generating recommendations via WebSocket: {e}")
            emit('error', {'message': 'Failed to generate recommendations'})
