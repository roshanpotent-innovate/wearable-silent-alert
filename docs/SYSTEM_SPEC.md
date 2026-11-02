# Wearable Silent Emergency Alert Band
## System Specification — Version 1.0

### 1. Project Objective

Develop a software prototype of a wearable emergency alert system that simulates sensor monitoring, detects potentially suspicious situations, requests discreet wearer confirmation, and escalates emergency incidents to a monitoring dashboard.

**Current scope:** Software simulation only. No physical sensors or actual police dispatch integration.

### 2. System Components

1. Virtual wearable simulator
2. Gesture and sensor-data evaluation
3. Emergency detection state machine
4. Confirmation and timeout manager
5. Incident management service
6. FastAPI backend
7. SQLite database
8. Police monitoring dashboard
9. Automated testing system

### 3. Detection Inputs

The virtual wearable will simulate:

- Gesture detection and configurable gesture patterns
- Heart rate in beats per minute
- Wearer acknowledgement
- Explicit SOS activation
- GPS coordinates
- GPS timestamp and accuracy
- Device connectivity and sensor availability

All simulated readings must be clearly identified as simulated.

### 4. Emergency Workflow

#### 4.1 Normal Monitoring

The system continuously evaluates simulated sensor readings.

High heart rate alone must not trigger an emergency.

Ordinary movement must not automatically trigger an emergency.

#### 4.2 Possible Distress

When a configured suspicious gesture pattern is detected, the system evaluates available supporting signals.

If the event meets the configured detection criteria, the system:

1. Creates a pending alert.
2. Simulates discreet wearable vibration.
3. Starts a configurable 15-second confirmation timer.

Normal heart rate must not automatically dismiss a suspicious gesture.

#### 4.3 Confirmation

The virtual wearer can respond using:

- A simulated physical button
- A simulated hand gesture

A valid safe acknowledgement cancels the pending escalation.

A help response triggers immediate escalation.

Invalid or ambiguous responses must not cancel the alert.

#### 4.4 Timeout

If the wearer does not respond before the timer expires, the system escalates the incident.

The timeout must expire independently of incoming sensor readings.

#### 4.5 Explicit SOS

An explicit SOS immediately initiates emergency escalation.

It must not depend on heart rate, other sensor readings, or wearer confirmation.

### 5. Incident Information

Each incident should contain:

- Unique incident ID
- Device ID
- Incident creation timestamp
- Alert reason
- Alert severity
- Incident state
- Latitude and longitude, when available
- Location timestamp
- Location accuracy, when available
- Simulation-mode indicator
- Delivery status

Missing or invalid location must not prevent emergency escalation.

The system must distinguish current location from stale location.

### 6. Incident States

The initial state model is:

MONITORING
    -> SUSPICIOUS
    -> AWAITING_CONFIRMATION
    -> CANCELLED or EMERGENCY

An explicit SOS can transition directly to EMERGENCY.

Delivery status is tracked separately from the incident state.

### 7. Delivery Management

The prototype will simulate alert delivery.

It must distinguish:

- PENDING
- SENDING
- DELIVERED
- FAILED

Failed deliveries should be retried according to a configurable policy.

The system must not report an alert as delivered without a successful acknowledgement from the simulated receiving service.

Network failure must not silently discard an incident.

Repeated events must not create unnecessary duplicate incidents.

### 8. Data Storage

SQLite will store incident records and relevant event history.

Active incidents must survive an application restart.

Cancelled incidents should remain available for auditing and testing.

### 9. Dashboard Requirements

The dashboard should display:

- Active incidents
- Incident ID and device ID
- Alert reason and severity
- Incident timestamp
- Location and location validity
- Incident state
- Delivery status
- Incident history

The interface must clearly identify simulated incidents.

No real police contact or dispatch will occur in the software-only prototype.

### 10. Required Test Scenarios

1. Normal movement
2. High heart rate without a suspicious gesture
3. Suspicious gesture with normal heart rate
4. Suspicious gesture followed by safe acknowledgement
5. Suspicious gesture followed by a help response
6. No response before timeout
7. Explicit SOS
8. Missing GPS
9. Stale GPS location
10. Invalid sensor data
11. Network disconnection and recovery
12. Duplicate event handling
13. Application restart with an active incident
14. Invalid acknowledgement
15. Sensor-data interruption

### 11. Safety and Validation Limitations

The system is a prototype, not a certified emergency-response product.

Simulated tests demonstrate software behaviour, not real-world detection accuracy.

Heart rate and movement cannot independently establish that an assault is occurring.

The prototype must not claim reliable assault prediction without appropriate evidence and validation.

Actual hardware integration and authorized emergency-service integration are outside the current implementation scope.

### 12. Implementation Roadmap

1. Finalize the detection state machine.
2. Implement the confirmation timer and acknowledgement handling.
3. Implement incident creation and metadata.
4. Develop the FastAPI backend and SQLite storage.
5. Implement simulated delivery and retry handling.
6. Build the monitoring dashboard.
7. Integrate components and run automated tests.
8. Document results and limitations.
9. Explore electronics simulation and hardware integration later.