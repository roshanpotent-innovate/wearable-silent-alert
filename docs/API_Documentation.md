# API Documentation – Wearable Silent Emergency Alert Band

**Document Version:** 1.0  
**Project:** Wearable Silent Emergency Alert Band  
**Backend Framework:** FastAPI  
**Programming Language:** Python  
**Communication Protocol:** HTTP  
**Data Format:** JSON

---

## 1. Introduction

The Wearable Silent Emergency Alert Band uses a REST-style API developed with FastAPI to enable communication between the frontend simulation dashboard and the backend alert management system.

The API receives simulated wearable readings, processes wearer responses, manages emergency incidents, and provides incident information to the dashboard.

The backend exposes six API endpoints covering:

1. Backend health monitoring.
2. Wearable reading submission.
3. Wearer response submission.
4. Retrieval of all incidents.
5. Retrieval of a specific incident.
6. Incident status updates.

All emergency notifications and dispatch operations are simulated. The current implementation does not contact real emergency services.

## 2. API Configuration

### 2.1 Backend Server

The backend is developed using FastAPI.

The development server runs on:

```text
http://localhost:8000
```

The interactive API documentation provided by FastAPI is available at:

```text
http://localhost:8000/docs
```

The alternative ReDoc documentation interface is available at:

```text
http://localhost:8000/redoc
```

### 2.2 Request and Response Format

The API uses JSON for request and response data.

| Property | Value |
|---|---|
| Protocol | HTTP |
| Request format | JSON |
| Response format | JSON |
| Content-Type | application/json |
| Backend framework | FastAPI |
| Data validation | Pydantic |

### 2.3 CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured to allow communication from the local frontend development server.

The permitted origins are:

```text
http://localhost:5173
http://127.0.0.1:5173
```

The configured HTTP methods are:

- GET
- POST

The permitted request header is:

- Content-Type

This configuration allows the React frontend and FastAPI backend to communicate while running on different local development ports.

## 3. API Endpoint Overview

The backend currently exposes the following endpoints.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend availability |
| POST | `/wearable/reading` | Submit simulated wearable readings |
| POST | `/wearable/response` | Submit SAFE or HELP response |
| GET | `/incidents` | Retrieve all incident records |
| GET | `/incidents/{incident_id}` | Retrieve a specific incident |
| POST | `/incidents/{incident_id}/status` | Update incident status |

## 4. Data Models and Validation

The backend uses Pydantic models to validate incoming JSON request data.

### 4.1 WearableReading Model

This model represents the data submitted by the wearable simulator.

| Field | Data Type | Required | Default / Validation |
|---|---|---|---|
| device_id | string | No | `WATCH-001` |
| heart_rate_bpm | integer or null | No | Default `null`, range 0–250 |
| gesture_detected | boolean | No | Default `false` |
| acknowledged | boolean or null | No | Default `null` |
| explicit_sos | boolean | No | Default `false` |
| latitude | float or null | No | Range -90 to 90 |
| longitude | float or null | No | Range -180 to 180 |
| location_accuracy_m | float or null | No | Minimum 0 |
| wearer_response | string or null | No | Default `null`; endpoint accepts only SAFE or HELP |

All fields are optional because the model defines default values.

**Important validation detail:** The `wearer_response` field is declared as a string in the Pydantic model. The `/wearable/reading` endpoint separately checks that its value is either `SAFE`, `HELP`, or `null`. An invalid value results in HTTP 422.

### 4.2 WearerResponse Model

This model is used when the wearer submits a response to a pending confirmation alert.

| Field | Data Type | Required | Default / Validation |
|---|---|---|---|
| device_id | string | No | `WATCH-001` |
| response | string literal | Yes | Must be `SAFE` or `HELP` |

The response field accepts only two values:

- `SAFE`: The wearer confirms that they are safe.
- `HELP`: The wearer requests emergency assistance.

### 4.3 IncidentStatusUpdate Model

This model is used to update an existing incident's management status.

| Field | Data Type | Required | Allowed Values |
|---|---|---|---|
| status | string literal | Yes | OPEN, ACKNOWLEDGED, DISPATCHED_SIMULATED, CLOSED |

The status must match one of the four supported values.

## 5. API Endpoint Documentation

### 5.1 Backend Health Check

**Endpoint:**

```http
GET /health
```

**Purpose:**

Checks whether the backend application is running and reports its operating mode.

**Request Body:** None.

**Example Response:**

```json
{
  "status": "ok",
  "mode": "simulation_only"
}
```

**Response Description:**

| Field | Description |
|---|---|
| status | Indicates backend health |
| mode | Indicates that the application operates in simulation mode |

**Expected Status Code:**

- `200 OK` – Backend is running.

### 5.2 Submit Wearable Reading

**Endpoint:**

```http
POST /wearable/reading
```

**Purpose:**

Receives simulated sensor readings and wearable events from the frontend simulator.

The backend passes the submitted data to the Alert Manager, which processes the reading and determines the appropriate action.

**Example Request:**

```json
{
  "device_id": "WATCH-001",
  "heart_rate_bpm": 135,
  "gesture_detected": true,
  "acknowledged": null,
  "explicit_sos": false,
  "latitude": 13.0827,
  "longitude": 80.2707,
  "location_accuracy_m": 10,
  "wearer_response": null
}
```

**Request Field Description:**

| Field | Description |
|---|---|
| device_id | Identifies the simulated wearable device |
| heart_rate_bpm | Simulated heart rate in BPM |
| gesture_detected | Indicates whether an emergency gesture was detected |
| acknowledged | Indicates whether the wearer acknowledged a confirmation prompt |
| explicit_sos | Indicates whether the wearer activated SOS |
| latitude | GPS latitude |
| longitude | GPS longitude |
| location_accuracy_m | Estimated GPS accuracy in metres |
| wearer_response | Optional SAFE or HELP response |

**Processing Flow:**

1. FastAPI validates the incoming request.
2. The backend converts the request model into a dictionary.
3. The Alert Manager processes the reading.
4. Explicit SOS and wearer responses are handled according to the alert management logic.
5. If an emergency is confirmed, the backend creates an incident record.
6. The API returns the processing result and incident information.

**Example Response – Confirmation Requested:**

```json
{
  "device_id": "WATCH-001",
  "timestamp": "2026-11-04T10:00:00+00:00",
  "result": {
    "alert_level": "SUSPICIOUS",
    "action": "REQUEST_CONFIRMATION",
    "reason": "Emergency gesture detected"
  },
  "incident_id": null,
  "delivery_status": null,
  "simulation_mode": true
}
```

The timestamp and reason shown are illustrative. The actual reason depends on the detection result.

**Example Response – Emergency Incident Generated:**

```json
{
  "device_id": "WATCH-001",
  "timestamp": "2026-11-04T10:00:00+00:00",
  "result": {
    "alert_level": "EMERGENCY",
    "action": "SEND_EMERGENCY_ALERT",
    "reason": "Explicit SOS activated"
  },
  "incident_id": "generated-incident-uuid",
  "delivery_status": "SIMULATED",
  "simulation_mode": true
}
```

The incident ID is generated by the backend and is different for each incident.

**Expected Status Codes:**

- `200 OK` – Reading processed successfully.
- `422 Unprocessable Entity` – Request validation failed, including invalid field values.

**Important Implementation Details:**

- An elevated heart rate by itself does not automatically generate an emergency incident.
- A suspicious event may initiate a confirmation process.
- An explicit SOS generates an immediate emergency result.
- An emergency incident is stored in SQLite.
- Alert delivery remains simulated.

### 5.3 Submit Wearer Response

**Endpoint:**

```http
POST /wearable/response
```

**Purpose:**

Receives the wearer's response to a pending confirmation alert.

The endpoint accepts either SAFE or HELP.

**Example Request – SAFE:**

```json
{
  "device_id": "WATCH-001",
  "response": "SAFE"
}
```

**Example Request – HELP:**

```json
{
  "device_id": "WATCH-001",
  "response": "HELP"
}
```

**Processing Flow:**

1. FastAPI validates the incoming response.
2. The backend forwards the device ID and response to the Alert Manager.
3. The Alert Manager checks the device's pending confirmation state.
4. The response is processed.
5. If HELP results in an emergency, an incident is created and stored.
6. If SAFE cancels a pending alert, no emergency incident is created.

**SAFE Response Behavior:**

- Removes an existing pending confirmation alert.
- Returns a NORMAL alert level with a cancellation action.
- Does not create an emergency incident.

If no pending alert exists, the Alert Manager returns a NORMAL result indicating that there is no pending alert for the device.

**HELP Response Behavior:**

- If a pending alert exists, the Alert Manager uses the original pending wearable reading when creating the emergency incident.
- If no pending alert exists, the response reading itself is used.
- An emergency incident is stored in SQLite.

**Example Response – SAFE:**

```json
{
  "device_id": "WATCH-001",
  "result": {
    "alert_level": "NORMAL",
    "action": "CANCEL_ALERT",
    "reason": "Wearer confirmed safety"
  },
  "incident_id": null,
  "delivery_status": null,
  "simulation_mode": true
}
```

**Example Response – HELP:**

```json
{
  "device_id": "WATCH-001",
  "result": {
    "alert_level": "EMERGENCY",
    "action": "SEND_EMERGENCY_ALERT",
    "reason": "Wearer requested help"
  },
  "incident_id": "generated-incident-uuid",
  "delivery_status": "SIMULATED",
  "simulation_mode": true
}
```

The example responses illustrate the main outcomes. Actual results depend on the pending confirmation state.

**Expected Status Codes:**

- `200 OK` – Response processed successfully.
- `422 Unprocessable Entity` – Missing or invalid request fields.

### 5.4 Retrieve All Incidents

**Endpoint:**

```http
GET /incidents
```

**Purpose:**

Retrieves all emergency incident records stored in the SQLite database.

**Request Body:** None.

**Processing Flow:**

1. The backend queries the `incidents` table.
2. Records are ordered by creation timestamp in descending order.
3. The records are returned to the frontend as JSON.

**Example Response:**

```json
[
  {
    "incident_id": "incident-uuid-001",
    "created_at": "2026-11-04T10:00:00+00:00",
    "device_id": "WATCH-001",
    "alert_level": "EMERGENCY",
    "status": "OPEN",
    "reason": "Explicit SOS activated",
    "heart_rate_bpm": 80,
    "latitude": 13.0827,
    "longitude": 80.2707,
    "location_accuracy_m": 10,
    "delivery_status": "SIMULATED"
  }
]
```

**Expected Status Codes:**

- `200 OK` – Incident records retrieved successfully.

If no incidents exist, the endpoint returns an empty JSON list.

### 5.5 Retrieve a Specific Incident

**Endpoint:**

```http
GET /incidents/{incident_id}
```

**Purpose:**

Retrieves a specific incident using its unique incident ID.

**Path Parameter:**

| Parameter | Data Type | Description |
|---|---|---|
| incident_id | string | Unique identifier of the requested incident |

**Example Request:**

```http
GET /incidents/incident-uuid-001
```

**Example Response:**

```json
{
  "incident_id": "incident-uuid-001",
  "created_at": "2026-11-04T10:00:00+00:00",
  "device_id": "WATCH-001",
  "alert_level": "EMERGENCY",
  "status": "OPEN",
  "reason": "Explicit SOS activated",
  "heart_rate_bpm": 80,
  "latitude": 13.0827,
  "longitude": 80.2707,
  "location_accuracy_m": 10,
  "delivery_status": "SIMULATED"
}
```

**Expected Status Codes:**

- `200 OK` – Incident found and returned.
- `404 Not Found` – No incident exists with the specified ID.

### 5.6 Update Incident Status

**Endpoint:**

```http
POST /incidents/{incident_id}/status
```

**Purpose:**

Updates the management status of an existing incident.

This endpoint allows the dashboard operator to record incident handling actions.

**Path Parameter:**

| Parameter | Data Type | Description |
|---|---|---|
| incident_id | string | Unique identifier of the incident |

**Request Body:**

```json
{
  "status": "ACKNOWLEDGED"
}
```

**Supported Status Values:**

| Status | Description |
|---|---|
| OPEN | Incident is awaiting operator action |
| ACKNOWLEDGED | Operator has acknowledged the incident |
| DISPATCHED_SIMULATED | Simulated dispatch has been recorded |
| CLOSED | Incident has been marked as closed |

**Processing Flow:**

1. The backend validates the requested status.
2. The database is checked to confirm that the incident exists.
3. If the incident exists, its status is updated.
4. The updated incident record is returned.

**Example Response:**

```json
{
  "incident": {
    "incident_id": "incident-uuid-001",
    "created_at": "2026-11-04T10:00:00+00:00",
    "device_id": "WATCH-001",
    "alert_level": "EMERGENCY",
    "status": "ACKNOWLEDGED",
    "reason": "Explicit SOS activated",
    "heart_rate_bpm": 80,
    "latitude": 13.0827,
    "longitude": 80.2707,
    "location_accuracy_m": 10,
    "delivery_status": "SIMULATED"
  },
  "simulation_mode": true,
  "message": "No real emergency service contacted"
}
```

**Expected Status Codes:**

- `200 OK` – Incident status updated successfully.
- `404 Not Found` – Incident does not exist.
- `422 Unprocessable Entity` – Invalid or unsupported status value.

**Important Implementation Detail:**

The backend validates the status value but does not enforce a mandatory status transition sequence.

For example, the backend accepts any of the four supported status values for an existing incident. The frontend dashboard applies additional restrictions to its status controls.

The `DISPATCHED_SIMULATED` status represents a simulated dispatch action and does not indicate that an actual emergency service was contacted.

## 6. Emergency Alert Processing and API Interaction

The following diagram illustrates the relationship between the frontend, API endpoints, Alert Manager, and database.

          POST/wearable/response
                  |
                  |
            Validate Request
                  |
                  |
              Response
                |   |
                |   |___________________
              SAFE                      |
                |                      HELP
                |                       |
          Cancel Pending Alert     Process Emergency Request
                |                       |
                |                       |
            Return Response        Generate Emergency Result
          No Incident Created           |
                                        |
                                   Store Incident in SQLite
                                        |
                                        |
                                    Return Response
                                  Incident ID Generated


The frontend also periodically retrieves incident records to refresh the incident dashboard.

## 7. Background Timeout Monitoring

The backend includes a background monitoring task that checks pending confirmation alerts.

The monitoring task:

1. Runs independently of incoming API requests.
2. Calls the Alert Manager's `check_timeouts()` method.
3. Checks whether any pending confirmation alert has exceeded the configured 15-second timeout.
4. Generates an emergency result for expired alerts.
5. Stores the resulting incident in SQLite.
6. Repeats the monitoring process approximately every second.

This mechanism allows emergency escalation to occur even if the wearer does not submit a SAFE or HELP response.

The timeout monitor operates within the FastAPI application lifecycle and is cancelled during application shutdown.

When a timeout expires, the Alert Manager removes the corresponding pending confirmation state and returns the original wearable reading with the emergency result. The background monitoring task then passes this information to **store_incident()** to create the incident record. This process occurs independently of a new frontend request.

## 8. Error Handling and Validation

The API uses Pydantic validation and explicit backend checks to reject invalid requests.

Common validation cases include:

| Condition | Expected HTTP Status |
|---|---|
| Missing required response field | 422 |
| Invalid wearer response | 422 |
| Heart rate below 0 or above 250 | HTTP 422 |
| Heart rate between 0-24 or 241-250 | Detection Engine returns **INVALID_READING** when evaluated |
| Heart rate between 25-240 | Accepted by both validation layers |
| Latitude outside -90 to 90 | 422 |
| Longitude outside -180 to 180 | 422 |
| Negative location accuracy | 422 |
| Invalid incident status | 422 |
| Incident ID not found | 404 |

The API uses HTTP 422 for request validation errors and HTTP 404 when a requested incident cannot be found.

## 9. API Security and Current Limitations

The current implementation is intended for local development and simulation.

Its limitations include:

1. No authentication or authorization mechanism is currently implemented.
2. No API key or token-based access control is configured.
3. CORS is configured for local frontend development origins.
4. No rate-limiting mechanism is implemented.
5. No real emergency notification integration exists.
6. The backend currently accepts simulated wearable readings rather than data from a physically connected wearable.
7. The system uses SQLite for local incident persistence.
8. The current implementation does not provide a production-grade deployment security configuration.

These limitations should be addressed before using the system in a real emergency-response environment.

## 10. Future API Enhancements

Potential future improvements include:

- Authentication and authorization for operators and wearable devices.
- Secure device registration and identification.
- HTTPS-based communication.
- Integration with SMS and emergency notification services.
- Real wearable sensor data ingestion.
- API rate limiting.
- Improved logging and monitoring.
- API versioning.
- Production deployment configuration.

These are proposed enhancements and are not currently implemented.

## 11. Conclusion

The FastAPI backend provides the communication interface between the Wearable Silent Emergency Alert Band frontend simulator and the emergency alert management system.

The six API endpoints support wearable reading submission, wearer response handling, incident retrieval, incident status management, and backend health monitoring.

Combined with the Alert Manager, Detection Engine, background timeout monitor, and SQLite database, the API implements the core communication and incident management functionality of the current simulation prototype.

All emergency alert and dispatch operations remain simulated, with no real emergency services contacted.