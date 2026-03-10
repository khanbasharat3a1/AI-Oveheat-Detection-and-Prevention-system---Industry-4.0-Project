
# Industrial Motor Health Monitoring System

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.2-green.svg)](https://flask.palletsprojects.com/)
[![Industrial IoT](https://img.shields.io/badge/Industrial-IoT-orange.svg)](https://github.com/your-repo)

*Real-time motor health monitoring with predictive analytics and automated maintenance recommendations.*

</div>

---

## Screenshots

<div align="center">

### Main Dashboard
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEgvjsT9ClM9sKrEEpc1RV1FcrwQmAAM2vxTVB-tFJPj6nYaG86llgIQtPW34E8hNKOBy9jAUY3PCZXwK0BNELbUZin5cTilecizLhun6esQeG_edg0tW0XRYNFBnAvkxnOG29xV0BF36NYmHJEKrcLFFx7x_o3cU6uDgRk4h048dFMiEpUMhUoE22929mA" alt="Main Dashboard" width="800"/>

### Real-time Analytics
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEgpB2bjuA6akNVF3N_zWXdx_U6RjcVl_bn-Yy5jaElDxlOW0i40RQSB1cAJf3gu49RcaXoPSX7PO8JOhcIuprM0EEJLx89cmSPpJ3D9k_vnQfKEnprJjbV6HkgMeirsHg1qx0oGlGuDu3FTp4Vmm6FwNyP0oXQM4_vPm_z8t_jayoF7BCPzpLXCvO_wb6k" alt="Analytics View" width="800"/>

### System Monitoring
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEib7kZWyCOO7gIANKxDg_RRMx1jJ8Kh8fgF22Socs6-GeajofweaHnWcZEtp2QhRQWsyLEoaPbTWYSICTYme9lydCLIxHnmZWuEb2DW29zB8c6eomM2nCM7t-Vvmf453xX9JJQSp_hGREEmZUz75AbFi6mDQhCRUfSHdGAKG4nbx6z0KZ04EnzxIdMSd1w" alt="Monitoring View" width="800"/>

### Health Analysis
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEiHqq3dkyo0jZEfUbiJCHIyHUWjvclXyIvykvDE00_aPprAsG_Tp-mA7Ek8pVQT5Ta27lYdtXbpvt07u8xiaQ2LV423C7o6kB5Nxc2r2KRXDry08MeRKQk-jw0DDhNdtAT5tVLcuH7kajthhkY9IYxRQDjfIuYcWKdfBRQooDmjYu0LqY5TIbVQvhy76dM" alt="Health Analysis" width="800"/>

</div>

---

## Features

**Health Analysis** — Four-category scoring (Electrical, Thermal, Mechanical, Predictive) using Isolation Forest anomaly detection with confidence-scored maintenance recommendations.

**Data Sources** — ESP32/Arduino sensors over WiFi (current, voltage, RPM, environment) and FX5U PLC via MC Protocol (motor temperature, voltage), with live WebSocket updates and CSV export.

**Monitored Parameters**

| Parameter | Optimal | Critical |
|-----------|---------|----------|
| Motor Temperature | < 40°C | > 60°C |
| System Voltage | 24V ± 10% | < 20V or > 28V |
| Motor Current | 6.25A | > 12A |
| Motor Speed | 2750 RPM | ±150 RPM |
| Environment | 24°C, 40% RH | > 40°C, > 70% RH |

---

## Project Structure

```
ai-motor-monitoring/
├── main.py
├── config.py
├── requirements.txt
├── .env
├── hardware/
│   ├── esp_handler.py
│   └── plc_manager.py
├── ai/
│   └── health_analyzer.py
├── database/
│   ├── models.py
│   └── manager.py
├── api/
│   └── routes.py
├── tests/
│   ├── esp_simulator.py
│   ├── plc_simulator.py
│   └── run_tests.py
├── templates/
│   └── dashboard.html
└── data/
    ├── sensor_data.csv
    └── motor_monitoring.db
```

---

## Setup

### Installation

```bash
git clone https://github.com/your-repo/ai-motor-monitoring.git
cd ai-motor-monitoring

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
mkdir -p data logs tests templates static
```

### Configuration

Create a `.env` file in the project root:

```env
PLC_IP=192.168.3.39
PLC_PORT=5007
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEBUG=True
DATABASE_URL=sqlite:///data/motor_monitoring.db
```

### Hardware

**FX5U PLC** — Enable MC Protocol on the Ethernet module, set IP to `192.168.3.39`, port `5007`. Use `D100` for voltage and `D102` for temperature.

**ESP32/Arduino** — Connect to the same WiFi network and point the device to `http://your-server:5000/send-data` using the JSON format below.

### Start

```bash
python main.py
# Dashboard at http://localhost:5000
```

---

## Testing

```bash
# ESP simulator (default: every 5 seconds)
python tests/esp_simulator.py --interval 5
python tests/esp_simulator.py --server http://192.168.1.100:5000 --duration 300

# PLC simulator
python tests/plc_simulator.py --ip 192.168.3.39 --interval 10
python tests/plc_simulator.py --test-only

# Combined
python tests/run_tests.py --duration 300
python tests/run_tests.py --duration 3600 --server http://localhost:5000
```

Expected ranges: voltage ~24V, current ~6.25A, RPM ~2650, motor temp ~28°C, humidity ~45%.

---

## API Reference

### REST

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/send-data` | POST | Ingest ESP sensor data |
| `/api/current-data` | GET | Live readings and health score |
| `/api/health-details` | GET | Per-category health breakdown |
| `/api/recommendations` | GET | Maintenance recommendations |
| `/api/historical-data` | GET | Historical chart data |
| `/api/maintenance-alerts` | GET | Active alerts |
| `/api/acknowledge-alert/<id>` | POST | Acknowledge an alert |
| `/api/motor-control` | POST | Send control commands |
| `/api/system-status` | GET | Full system status |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Client → Server | Establish connection |
| `sensor_update` | Server → Client | Live sensor readings |
| `health_update` | Server → Client | Health score changes |
| `recommendations_update` | Server → Client | New recommendations |
| `maintenance_alert` | Server → Client | Critical alerts |
| `connection_lost` | Server → Client | Hardware disconnection |
| `status_update` | Server → Client | System state changes |
| `request_update` | Client → Server | Manual refresh |

### ESP Payload Format

```json
{
  "TYPE": "ADU_TEXT",
  "VAL1": "6.25",
  "VAL2": "24.0",
  "VAL3": "2650",
  "VAL4": "26.0",
  "VAL5": "45.0",
  "VAL6": "78.8",
  "VAL7": "27.2",
  "VAL8": "81.0",
  "VAL9": "OFF",
  "VAL10": "OFF",
  "VAL11": "OFF",
  "VAL12": "NOR"
}
```

Fields: VAL1 current (A), VAL2 voltage (V), VAL3 RPM, VAL4 temperature (°C), VAL5 humidity (%), VAL6 temperature (°F), VAL7–8 heat index, VAL9–11 relay status, VAL12 combined status.

---

## Health Scoring

| Category | Weight | Factors |
|----------|--------|---------|
| Electrical | 30% | Voltage, current, over/underload |
| Thermal | 35% | Motor temp, ambient conditions, humidity |
| Mechanical | 25% | RPM deviation, load balance |
| Predictive | 10% | Temperature trends, current stability |

| Score | Status | Action |
|-------|--------|--------|
| 90–100 | Excellent | Continue monitoring |
| 75–89 | Good | Routine maintenance |
| 60–74 | Warning | Schedule inspection |
| 0–59 | Critical | Stop operation |

---

## Configuration Reference

Edit `config.py` to adjust thresholds:

```python
MOTOR_TEMP_CRITICAL = 60.0      # °C
MOTOR_TEMP_WARNING  = 50.0      # °C
MOTOR_TEMP_OPTIMAL  = 40.0      # °C

VOLTAGE_MIN_CRITICAL = 20.0     # V
VOLTAGE_MAX_CRITICAL = 28.0     # V

CURRENT_OPTIMAL      = 6.25     # A
CURRENT_MAX_WARNING  = 9.0      # A
CURRENT_MAX_CRITICAL = 12.0     # A

RPM_OPTIMAL      = 2750         # RPM
RPM_MIN_WARNING  = 2600         # RPM
RPM_MAX_WARNING  = 2900         # RPM

ESP_TIMEOUT             = 30    # seconds
PLC_TIMEOUT             = 60    # seconds
DATA_CLEANUP_INTERVAL   = 10    # seconds
```

---

## Troubleshooting

<details>
<summary><b>ESP not sending data</b></summary>

Verify network reachability and test the endpoint manually:

```bash
curl -X POST http://localhost:5000/send-data \
  -H "Content-Type: application/json" \
  -d '{"TYPE":"TEST","VAL1":"6.25","VAL2":"24.0"}'
```
</details>

<details>
<summary><b>PLC connection refused</b></summary>

```python
import pymcprotocol
mc = pymcprotocol.Type3E()
print(mc.connect('192.168.3.39', 5007))
```

Check that MC Protocol is enabled on the FX5U, port 5007 is open, and the IP matches `.env`.
</details>

<details>
<summary><b>Database errors</b></summary>

```bash
rm data/motor_monitoring.db
python main.py
```
</details>

<details>
<summary><b>Port 5000 already in use</b></summary>

```bash
# Linux/Mac
lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

Set a different port: `FLASK_PORT=5001` in `.env`.
</details>

---

## Extending the System

**New sensors** — Parse new fields in `hardware/esp_handler.py`, add columns to `database/models.py`, update scoring in `ai/health_analyzer.py`, and reflect changes in `templates/dashboard.html`.

**Custom models** — Extend `ai/health_analyzer.py` with additional algorithms, persist models with joblib, and update the recommendation engine accordingly.

**New API endpoints** — Add routes in `api/routes.py`, wire up WebSocket events, and document here.

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m 'Add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a pull request

---

## Contact

khanbasharat3a1@gmail.com

<div align="center">

[![Star on GitHub](https://img.shields.io/github/stars/your-repo/ai-motor-monitoring.svg?style=social)](https://github.com/khanbasharat3a1/AI-Oveheat-Detection-and-Prevention-system---Industry-4.0-Project)
[![Follow on GitHub](https://img.shields.io/github/followers/your-username.svg?style=social&label=Follow)](https://github.com/khanbasharat3a1)

</div>