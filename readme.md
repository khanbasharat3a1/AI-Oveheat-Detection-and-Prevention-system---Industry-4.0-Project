# 🔧 AI-Enabled Industrial Motor Health Monitoring System

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.2-green.svg)](https://flask.palletsprojects.com/)
[![Industrial IoT](https://img.shields.io/badge/Industrial-IoT-orange.svg)](https://github.com/your-repo)
[![AI Powered](https://img.shields.io/badge/AI-Powered-purple.svg)](https://github.com/your-repo)

*A comprehensive, AI-powered motor health monitoring system with real-time data acquisition, predictive analytics, and intelligent maintenance recommendations.*

</div>

---

## 📸 System Dashboard Screenshots

<div align="center">
  
### Main Dashboard View
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEgvjsT9ClM9sKrEEpc1RV1FcrwQmAAM2vxTVB-tFJPj6nYaG86llgIQtPW34E8hNKOBy9jAUY3PCZXwK0BNELbUZin5cTilecizLhun6esQeG_edg0tW0XRYNFBnAvkxnOG29xV0BF36NYmHJEKrcLFFx7x_o3cU6uDgRk4h048dFMiEpUMhUoE22929mA" alt="Main Dashboard" width="800"/>

### Real-time Analytics
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEgpB2bjuA6akNVF3N_zWXdx_U6RjcVl_bn-Yy5jaElDxlOW0i40RQSB1cAJf3gu49RcaXoPSX7PO8JOhcIuprM0EEJLx89cmSPpJ3D9k_vnQfKEnprJjbV6HkgMeirsHg1qx0oGlGuDu3FTp4Vmm6FwNyP0oXQM4_vPm_z8t_jayoF7BCPzpLXCvO_wb6k" alt="Analytics View" width="800"/>

### System Monitoring
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEib7kZWyCOO7gIANKxDg_RRMx1jJ8Kh8fgF22Socs6-GeajofweaHnWcZEtp2QhRQWsyLEoaPbTWYSICTYme9lydCLIxHnmZWuEb2DW29zB8c6eomM2nCM7t-Vvmf453xX9JJQSp_hGREEmZUz75AbFi6mDQhCRUfSHdGAKG4nbx6z0KZ04EnzxIdMSd1w" alt="Monitoring View" width="800"/>

### Health Analysis Dashboard
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEiHqq3dkyo0jZEfUbiJCHIyHUWjvclXyIvykvDE00_aPprAsG_Tp-mA7Ek8pVQT5Ta27lYdtXbpvt07u8xiaQ2LV423C7o6kB5Nxc2r2KRXDry08MeRKQk-jw0DDhNdtAT5tVLcuH7kajthhkY9IYxRQDjfIuYcWKdfBRQooDmjYu0LqY5TIbVQvhy76dM" alt="Health Analysis" width="800"/>

</div>

---

## ✨ Key Features

### 🤖 AI-Powered Health Analysis
- **4-Category Health Assessment**: Electrical, Thermal, Mechanical, Predictive
- **Real-time Anomaly Detection** using Isolation Forest algorithms
- **Predictive Maintenance** with confidence scoring
- **Smart Recommendations** based on operational patterns

### 📡 Multi-Source Data Integration
- **ESP32/Arduino** sensor data via WiFi (Current, Voltage, RPM, Environment)
- **FX5U PLC** communication via MC Protocol (Motor temperature, Voltage)
- **Real-time WebSocket** updates for live dashboard
- **CSV Export** for external analysis

### 📊 Comprehensive Monitoring
- **Motor Parameters**: 24V DC motor optimized thresholds
- **Environmental Conditions**: Temperature, Humidity, Heat Index
- **Relay Status Monitoring**: 3-channel protection relays
- **Connection Health**: Automatic timeout detection and alerts

### 🎯 Optimal Value Targeting
| Parameter | Optimal Range | Critical Limits |
|-----------|--------------|-----------------|
| Motor Temperature | < 40°C | > 60°C |
| System Voltage | 24V ± 10% | < 20V or > 28V |
| Motor Current | 6.25A | > 12A |
| Motor Speed | 2750 RPM | ± 150 RPM |
| Environment | 24°C, 40% RH | > 40°C, > 70% RH |

---

## 🏗️ System Architecture

```
📁 ai-motor-monitoring/
├── 📄 main.py                    # Application entry point
├── ⚙️ config.py                  # System configuration
├── 📦 requirements.txt           # Dependencies
├── 🔐 .env                       # Environment variables
│
├── 🔌 hardware/                  # Hardware communication
│   ├── esp_handler.py           # ESP/Arduino interface
│   └── plc_manager.py           # FX5U PLC MC protocol
│
├── 🧠 ai/                        # AI & Analytics
│   └── health_analyzer.py       # Health analysis & recommendations
│
├── 💾 database/                  # Data management
│   ├── models.py                # SQLAlchemy models
│   └── manager.py               # Database operations
│
├── 🌐 api/                       # Web API
│   └── routes.py                # REST endpoints & WebSocket
│
├── 🧪 tests/                     # Test scripts
│   ├── esp_simulator.py         # ESP data simulator
│   ├── plc_simulator.py         # PLC data simulator
│   └── run_tests.py             # Test runner
│
├── 🎨 templates/                 # Web interface
│   └── dashboard.html           # Main dashboard
│
└── 📊 data/                      # Data storage
    ├── sensor_data.csv          # CSV exports
    └── motor_monitoring.db      # SQLite database
```

---

## 🚀 Quick Start Guide

### 1️⃣ Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/ai-motor-monitoring.git
cd ai-motor-monitoring

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p data logs tests templates static
```

### 2️⃣ Configuration

Create `.env` file in the project root:

```env
# PLC Configuration
PLC_IP=192.168.3.39
PLC_PORT=5007

# Flask Configuration  
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=True

# Database
DATABASE_URL=sqlite:///data/motor_monitoring.db
```

### 3️⃣ Hardware Setup

#### 🔧 FX5U PLC Configuration
1. Enable MC Protocol on Ethernet module
2. Set IP: `192.168.3.39` (or update `.env`)
3. Port: `5007`
4. Configure `D100` for voltage monitoring
5. Configure `D102` for temperature monitoring

#### 📡 ESP32/Arduino Network
1. Connect to WiFi network
2. Configure server IP in ESP code
3. Send data to: `http://your-server:5000/send-data`
4. JSON format with `VAL1-VAL12` fields

### 4️⃣ Run the System

```bash
# Start the main application
python main.py

# Access dashboard at: http://localhost:5000
```

---

## 🧪 Testing Suite

### Simulate ESP Data
```bash
# Start ESP simulator (sends data every 5 seconds)
python tests/esp_simulator.py --interval 5

# Custom server and duration
python tests/esp_simulator.py --server http://192.168.1.100:5000 --duration 300
```

### Simulate PLC Data
```bash
# Start PLC simulator (writes every 10 seconds)
python tests/plc_simulator.py --ip 192.168.3.39 --interval 10

# Test connection only
python tests/plc_simulator.py --test-only
```

### Run Combined Tests
```bash
# Run both simulators for 5 minutes
python tests/run_tests.py --duration 300

# Full system test
python tests/run_tests.py --duration 3600 --server http://localhost:5000
```

### 📈 Expected Test Values
- **Voltage**: ~24V (22V-26V range)
- **Current**: ~6.25A (4A-9A range)  
- **RPM**: ~2650 (2400-2900 range)
- **Motor Temperature**: ~28°C (23°C-43°C range)
- **Environment**: ~26°C, ~45% humidity

---

## 📡 API Documentation

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/send-data` | POST | Receive ESP sensor data |
| `/api/current-data` | GET | Current readings & health |
| `/api/health-details` | GET | Detailed health breakdown |
| `/api/recommendations` | GET | AI recommendations |
| `/api/historical-data` | GET | Historical data for charts |
| `/api/maintenance-alerts` | GET | Active maintenance alerts |
| `/api/acknowledge-alert/<id>` | POST | Acknowledge alert |
| `/api/motor-control` | POST | Motor control commands |
| `/api/system-status` | GET | Complete system status |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Client connection |
| `sensor_update` | Server → Client | Real-time sensor data |
| `health_update` | Server → Client | Health score updates |
| `recommendations_update` | Server → Client | New recommendations |
| `maintenance_alert` | Server → Client | Critical alerts |
| `connection_lost` | Server → Client | Hardware disconnection |
| `status_update` | Server → Client | System status changes |
| `request_update` | Client → Server | Manual update request |

### ESP Data Format

```json
{
  "TYPE": "ADU_TEXT",
  "VAL1": "6.25",     // Current (A)
  "VAL2": "24.0",     // Voltage (V)
  "VAL3": "2650",     // RPM
  "VAL4": "26.0",     // Temperature (°C)
  "VAL5": "45.0",     // Humidity (%)
  "VAL6": "78.8",     // Temperature (°F)
  "VAL7": "27.2",     // Heat Index (°C)
  "VAL8": "81.0",     // Heat Index (°F)
  "VAL9": "OFF",      // Relay 1 Status
  "VAL10": "OFF",     // Relay 2 Status
  "VAL11": "OFF",     // Relay 3 Status
  "VAL12": "NOR"      // Combined Status
}
```

---

## 🏥 Health Analysis System

### Health Categories

| Category | Weight | Description | Key Factors |
|----------|--------|-------------|-------------|
| **Electrical** | 30% | Voltage, Current Analysis | Under/overvoltage, overcurrent, underload |
| **Thermal** | 35% | Temperature Management | Motor temp, ambient conditions, humidity |
| **Mechanical** | 25% | Mechanical Performance | RPM deviations, load balance, vibration |
| **Predictive** | 10% | Trend Analysis | Temperature trends, current stability, degradation |

### Health Score Ranges

| Score | Status | Description | Action |
|-------|--------|-------------|--------|
| **90-100** | 🟢 Excellent | Optimal performance | Continue monitoring |
| **75-89** | 🟡 Good | Normal operation | Routine maintenance |
| **60-74** | 🟠 Warning | Attention needed | Schedule inspection |
| **0-59** | 🔴 Critical | Immediate action required | Stop operation |

### AI Recommendations
- **Connection Alerts**: Hardware communication issues
- **Performance Optimization**: Load balancing suggestions
- **Maintenance Scheduling**: Predictive maintenance timing
- **Safety Warnings**: Critical condition alerts
- **Efficiency Improvements**: Energy optimization tips

---

## 💾 Data Management

### Database Schema
- **sensor_data**: Real-time sensor readings with health scores
- **maintenance_log**: Alerts and recommendations with confidence levels
- **system_events**: System operations and manual commands

### CSV Export Features
- Timestamp with all sensor readings
- Calculated health scores (4 categories + overall)
- Power consumption and efficiency metrics
- Relay status and system state
- Automatic hourly/daily exports

---

## ⚙️ Configuration Options

### Motor Thresholds

Edit `config.py` to customize thresholds:

```python
# Motor Temperature
MOTOR_TEMP_CRITICAL = 60.0      # °C
MOTOR_TEMP_WARNING = 50.0       # °C  
MOTOR_TEMP_OPTIMAL = 40.0       # °C

# Voltage (24V System)
VOLTAGE_MIN_CRITICAL = 20.0     # V
VOLTAGE_MAX_CRITICAL = 28.0     # V

# Current  
CURRENT_OPTIMAL = 6.25          # A
CURRENT_MAX_WARNING = 9.0       # A
CURRENT_MAX_CRITICAL = 12.0     # A

# RPM
RPM_OPTIMAL = 2750              # RPM
RPM_MIN_WARNING = 2600          # RPM
RPM_MAX_WARNING = 2900          # RPM
```

### Connection Timeouts

```python
ESP_TIMEOUT = 30                # seconds
PLC_TIMEOUT = 60                # seconds  
DATA_CLEANUP_INTERVAL = 10      # seconds
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

<details>
<summary><b>📡 ESP Connection Problems</b></summary>

Check network connectivity:
```bash
ping 192.168.1.100
```

Verify ESP is sending data:
```bash
curl -X POST http://localhost:5000/send-data \
  -H "Content-Type: application/json" \
  -d '{"TYPE":"TEST","VAL1":"6.25","VAL2":"24.0"}'
```
</details>

<details>
<summary><b>🔌 PLC Connection Issues</b></summary>

Test PLC connectivity:
```python
import pymcprotocol
mc = pymcprotocol.Type3E()
print('Connected:', mc.connect('192.168.3.39', 5007))
```

**Checklist:**
- ✅ Verify MC Protocol settings on FX5U
- ✅ Confirm port 5007 is enabled
- ✅ Check IP address matches configuration
</details>

<details>
<summary><b>💾 Database Errors</b></summary>

Reset database:
```bash
rm data/motor_monitoring.db
python main.py
```
</details>

<details>
<summary><b>🔒 Port Already in Use</b></summary>

Find process using port 5000:
```bash
# On Linux/Mac
lsof -i :5000

# On Windows
netstat -ano | findstr :5000
```

Change port in `.env` file:
```bash
echo "FLASK_PORT=5001" >> .env
```
</details>

---

## 👨‍💻 Development

### Adding New Sensors
1. Update `hardware/esp_handler.py` to parse new data fields
2. Add corresponding columns to `database/models.py`
3. Modify health analysis in `ai/health_analyzer.py`
4. Update dashboard display in `templates/dashboard.html`

### Custom AI Models
1. Extend `ai/health_analyzer.py` with new algorithms
2. Add model persistence using joblib
3. Create training scripts in `ai/` directory
4. Update recommendation engine with new insights

### API Extensions
1. Add new endpoints in `api/routes.py`
2. Update WebSocket events for real-time features
3. Document new API endpoints in README
4. Create client examples in `examples/` directory

---


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 💬 Support & Resources

- **📧 Email**: khanbasharat3a1@gmail.com


---

<div align="center">

**Built for Industrial IoT Excellence** | **Powered by AI** | **Data-Driven Insights**

Made with ❤️ by Khan Basharat

[![Star on GitHub](https://img.shields.io/github/stars/your-repo/ai-motor-monitoring.svg?style=social)](https://github.com/khanbasharat3a1/AI-Oveheat-Detection-and-Prevention-system---Industry-4.0-Project)
[![Follow on GitHub](https://img.shields.io/github/followers/your-username.svg?style=social&label=Follow)](https://github.com/khanbasharat3a1)

</div>