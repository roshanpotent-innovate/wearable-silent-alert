# Wearable Silent Emergency Alert Band

A software-based prototype for detecting potential emergencies through simulated wearable readings, requesting wearer confirmation, and generating emergency incident records for operator review.

## 1. Project Overview

The Wearable Silent Emergency Alert Band is designed around a simple objective: provide a mechanism for identifying potential emergency situations when a wearer may be unable to communicate their need for help verbally.

The prototype simulates wearable sensor readings and processes them through a rule-based detection and alert-management system.

When suspicious activity is detected, the system requests confirmation from the wearer. If the wearer requests help, explicitly activates SOS, or fails to respond within the configured confirmation period, the system generates an emergency incident.

A web dashboard allows an operator to monitor simulated device activity, view incidents, inspect available location information, and update incident statuses.

**Important:** This repository currently implements a software simulation prototype. It does not yet connect to a physical wearable device or contact real emergency services.

## 2. Key Features

### Emergency Detection
- Processes simulated heart-rate readings.
- Detects suspicious gesture activity.
- Evaluates combinations of gesture and elevated heart rate.
- Supports explicit SOS activation.
- Validates incoming wearable readings.

### Wearer Confirmation
- Requests confirmation when suspicious activity is detected.
- Supports SAFE and HELP responses.
- Cancels pending alerts when the wearer confirms safety.
- Escalates an alert when the confirmation timeout expires.

### Emergency Incident Management
- Generates unique incident IDs.
- Stores incident timestamps and device information.
- Records alert reasons and available heart-rate and location data.
- Supports incident status updates.
- Maintains incident records using SQLite.

### Monitoring Dashboard
- Simulates wearable device scenarios.
- Displays detection and alert states.
- Provides SAFE and HELP controls.
- Displays a confirmation countdown.
- Lists and filters emergency incidents.
- Displays incident details and available location information.
- Provides operator controls for incident status updates.

## 3. System Architecture

The prototype consists of three main layers:

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite | Dashboard and wearable simulation |
| Backend | Python, FastAPI | Detection, alert management, API endpoints |
| Database | SQLite | Persistent emergency incident records |

### Emergency Processing Flow

1. The frontend sends a simulated wearable reading to the backend.
2. The Alert Manager processes the reading.
3. Explicit SOS and wearer HELP responses trigger emergency handling.
4. Other readings are evaluated by the Detection Engine when no confirmation is already pending.
5. Suspicious activity creates a pending confirmation state.
6. A SAFE response cancels the pending alert.
7. A HELP response or expired confirmation timeout generates an emergency incident.
8. The backend stores the incident in SQLite.
9. The dashboard retrieves and displays incident information.

## 4. Technology Stack

**Frontend**
- React 19
- TypeScript
- Vite
- CSS

**Backend**
- Python
- FastAPI
- Pydantic
- Uvicorn

**Database**
- SQLite

**Testing**
- Pytest
- FastAPI TestClient

## 5. Project Structure

## Project Structure

```text
wearable-silent-alert/
│
├── backend/
│   ├── main.py
│   ├── alert_manager.py
│   ├── detection_engine.py
│   ├── database.py
│   ├── test_alert_manager.py
│   ├── test_api.py
│   ├── test_detection_engine.py
│   └── incidents.db              # Generated SQLite database
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── simulation/
│   ├── run_simulation.py
│   └── wearable_simulator.py
│
├── docs/
│   ├── API_Documentation.md
│   ├── Database_Design.md
│   ├── Data_Flow_Diagram.md
│   └── System_Architecture.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Simulation

The project includes two different simulation approaches.

### 1. Standalone wearable simulator

File: `simulation/wearable_simulator.py`

This script generates synthetic wearable readings using randomly selected scenarios:

- Normal
- Normal movement
- Elevated heart rate
- Possible distress
- Explicit SOS

Each generated reading includes a device ID, timestamp, heart rate, gesture detection, acknowledgement state, SOS state, scenario name, and simulation-mode indicator.

### 2. Detection engine simulation

File: `simulation/run_simulation.py`

This script repeatedly:
1. Generates a synthetic wearable reading.
2. Passes the reading directly to the backend Detection Engine.
3. Displays the generated sensor data.
4. Displays the detection result.
5. Prints a simulated emergency alert if the engine returns `SEND_EMERGENCY_ALERT`.
6. Waits three seconds before generating another reading.

Run it from the project root:

```powershell
python simulation/run_simulation.py
```

Stop it using `Ctrl + C`.

**Note:** This standalone simulation tests the Detection Engine directly. It does not exercise the FastAPI endpoints, Alert Manager confirmation timeout, or SQLite incident storage.

### 3. Dashboard-based simulation

The React dashboard provides a separate interactive simulation interface connected to the FastAPI backend.

It allows users to:
- Select predefined wearable scenarios.
- Simulate normal and suspicious readings.
- Trigger explicit SOS.
- Respond with SAFE or HELP.
- Observe confirmation countdowns.
- View generated emergency incidents.
- Manage incident statuses.

This approach exercises the integrated backend alert-management workflow rather than only the Detection Engine.

## 6. Getting Started

### Prerequisites

Install the following before running the project:

- Python 3.10 or later
- Node.js and npm
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/roshanpotent-innovate/wearable-silent-alert.git
cd wearable-silent-alert
```

### Step 2: Set Up the Backend

Create and activate a Python virtual environment:

**Windows PowerShell**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```powershell
pip install -r ..\requirements.txt
```

Start the FastAPI server:

```powershell
python -m uvicorn main:app --reload --port 8000
```

The backend will be available at:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

The SQLite database is initialized by the backend when the application starts.

### Step 3: Set Up the Frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite development URL shown in the terminal, normally:

http://localhost:5173

Keep both the backend and frontend running while using the dashboard.

## 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks backend availability |
| POST | `/wearable/reading` | Submits a simulated wearable reading |
| POST | `/wearable/response` | Submits a SAFE or HELP response |
| GET | `/incidents` | Retrieves all incident records |
| GET | `/incidents/{incident_id}` | Retrieves a specific incident |
| POST | `/incidents/{incident_id}/status` | Updates an incident status |

For request bodies, response formats, validation rules, and examples, see [API Documentation](docs/API_Documentation.md).

## 8. Detection and Alert Logic

The prototype uses rule-based detection rather than a trained machine-learning model.

| Input condition | Expected behavior |
|---|---|
| Normal reading | Continue monitoring |
| Suspicious gesture | Request wearer confirmation |
| Elevated heart rate alone | Continue monitoring |
| Gesture with elevated heart rate, no acknowledgement | Request confirmation |
| Gesture with elevated heart rate and negative acknowledgement | Generate emergency alert |
| Gesture with elevated heart rate and positive acknowledgement | Continue monitoring |
| Explicit SOS | Generate emergency alert immediately |
| HELP response | Generate emergency alert |
| SAFE response | Cancel pending alert |
| Confirmation timeout | Generate emergency alert |

The confirmation timeout is configured to 15 seconds in the current backend.

**Important:** Once a confirmation is pending, ordinary readings for that device wait for the wearer's response or timeout rather than being independently re-evaluated by the Detection Engine.

## 9. Testing

Backend tests are implemented using Pytest.

From the repository root, activate the backend virtual environment and run:

```powershell
python -m pytest backend -v
```

The previously verified test suite completed with **20 passing tests**.

Frontend quality checks:

```powershell
cd frontend
npm run lint
npm run build
```

Both frontend checks have also passed in the development workflow.

## 10. Simulation Scenarios

The dashboard provides scenarios for testing the alert workflow:

1. Normal Movement
2. Suspicious Gesture
3. High Heart Rate
4. Gesture + High Heart Rate
5. Trigger SOS
6. SOS Without GPS

Synthetic location coordinates are used for simulation scenarios where location is included.

The dashboard can also simulate wearer responses and allow an operator to update incident statuses.

## 11. Current Limitations

This is a software prototype, not a production-ready emergency response device.

Current limitations include:

- No physical wearable or sensor integration.
- No real-time heart-rate sensor acquisition.
- No actual gesture sensor acquisition.
- No real GPS hardware integration.
- No SMS or telephone notifications.
- No police, ambulance, or emergency-service integration.
- No automatic real-world dispatch.
- Detection is rule-based and has not been validated for real-world medical or emergency accuracy.
- Location data used in simulator scenarios is synthetic.

All emergency delivery statuses are simulated. The system must not be relied upon for real emergency protection.

## 12. Project Documentation

Detailed technical documentation is available in the `docs/` directory:

| Document | Description |
|---|---|
| [System Architecture](docs/System_Architecture.md) | Overall architecture and component responsibilities |
| [Data Flow Diagram](docs/Data_Flow_Diagram.md) | Data movement and emergency processing flow |
| [Database Design](docs/Database_Design.md) | SQLite schema and incident storage |
| [API Documentation](docs/API_Documentation.md) | API endpoints, request models, and responses |

## 13. Future Development

Potential future development directions include:

- Integration with physical wearable sensors.
- Real GPS hardware integration.
- Improved detection algorithms using validated datasets.
- Secure communication between wearable devices and backend.
- Reliable notification infrastructure.
- Integration with authorized emergency response services.
- Deployment and field testing under controlled conditions.

These are future development directions and are not implemented features of the current prototype.

---

**Project:** Wearable Silent Emergency Alert Band  
**Repository:** [GitHub](https://github.com/roshanpotent-innovate/wearable-silent-alert)  
**Project Type:** Software simulation prototype