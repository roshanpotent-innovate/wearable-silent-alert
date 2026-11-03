import { useCallback, useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

type Incident = {
  incident_id: string;
  created_at: string;
  device_id: string | null;
  alert_level: string;
  status: string;
  reason: string | null;
  heart_rate_bpm: number | null;
  latitude: number | null;
  longitude: number | null;
  location_accuracy_m: number | null;
  delivery_status: string;
};

type ApiResponse = {
  detail?: string;
  device_id?: string;
  result?: {
    action?: string;
    alert_level?: string;
    reason?: string;
    seconds_remaining?: number;
  };
  incident_id?: string | null;
  delivery_status?: string | null;
  simulation_mode?: boolean;
};

type SimulationReading = {
  heart_rate_bpm: number;
  gesture_detected: boolean;
  explicit_sos?: boolean;
  latitude?: number;
  longitude?: number;
  location_accuracy_m?: number;
};

type PendingConfirmation = {
  deviceId: string;
  expiresAt: number;
};

const statuses = [
  "ALL",
  "OPEN",
  "ACKNOWLEDGED",
  "DISPATCHED_SIMULATED",
  "CLOSED",
];

const DEMO_LOCATION = {
  latitude: 13.0827,
  longitude: 80.2707,
  location_accuracy_m: 10,
};

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [simulating, setSimulating] = useState(false);

  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");

  const [apiOnline, setApiOnline] = useState(false);
  const [deviceId, setDeviceId] = useState("WATCH-001");

  const [pendingConfirmation, setPendingConfirmation] =
    useState<PendingConfirmation | null>(null);

  const [clock, setClock] = useState(0);

  const loadIncidents = useCallback(async () => {
    try {
      const response = await fetch(`${API}/incidents`);

      if (!response.ok) {
        throw new Error("Could not load incidents.");
      }

      const data: Incident[] = await response.json();

      setIncidents(data);
      setApiOnline(true);

      setSelectedId((current) => {
        if (current && data.some((item) => item.incident_id === current)) {
          return current;
        }

        return data[0]?.incident_id ?? null;
      });

      setError("");
    } catch {
      setApiOnline(false);
      setError("Backend unavailable. Check that the FastAPI server is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
  const initialLoad = window.setTimeout(() => {
    void loadIncidents();
  }, 0);

  const refreshTimer = window.setInterval(() => {
    void loadIncidents();
  }, 3000);

  const clockTimer = window.setInterval(() => {
    setClock(Date.now());
  }, 250);

  return () => {
    window.clearTimeout(initialLoad);
    window.clearInterval(refreshTimer);
    window.clearInterval(clockTimer);
  };
}, [loadIncidents]);

  // Update the confirmation countdown while an alert is pending.
  useEffect(() => {
    if (!pendingConfirmation) return;

    const timer = window.setInterval(() => {
      setClock(Date.now());
    }, 250);

    return () => window.clearInterval(timer);
  }, [pendingConfirmation]);

  const secondsRemaining = pendingConfirmation
    ? Math.max(
        0,
        Math.ceil((pendingConfirmation.expiresAt - clock) / 1000),
      )
    : 0;

  const visibleIncidents =
    filter === "ALL"
      ? incidents
      : incidents.filter((incident) => incident.status === filter);

  const selected = incidents.find(
    (incident) => incident.incident_id === selectedId,
  );

  const openCount = incidents.filter(
    (incident) => incident.status === "OPEN",
  ).length;

  const emergencyCount = incidents.filter(
    (incident) => incident.alert_level === "EMERGENCY",
  ).length;

  const activeCount = incidents.filter(
    (incident) => incident.status !== "CLOSED",
  ).length;

  const hasPendingForDevice =
    pendingConfirmation?.deviceId === deviceId.trim();

  async function submitReading(
    scenarioName: string,
    reading: SimulationReading,
  ) {
    const currentDevice = deviceId.trim();

    if (!currentDevice) {
      setError("Enter a device ID before running a simulation.");
      return;
    }

    setSimulating(true);
    setError("");
    setFeedback("");

    try {
      const response = await fetch(`${API}/wearable/reading`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          device_id: currentDevice,
          ...reading,
        }),
      });

      const data: ApiResponse = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ??
            "The simulation request failed.",
        );
      }

      const action = data.result?.action;
      const reason = data.result?.reason;

      if (
        action === "REQUEST_CONFIRMATION" ||
        action === "WAITING_FOR_CONFIRMATION"
      ) {
        const remaining = data.result?.seconds_remaining ?? 15;

        setPendingConfirmation({
          deviceId: currentDevice,
          expiresAt: clock + remaining * 1000,
        });

        setFeedback(
          `${scenarioName}: confirmation requested. The wearer has ${remaining} seconds to respond.`,
        );
      } else if (data.incident_id) {
        setPendingConfirmation(null);

        setFeedback(
          `${scenarioName}: emergency incident created successfully. Incident ID: ${data.incident_id}`,
        );
      } else {
        if (
          action === "CANCEL_ALERT" ||
          action === "CONTINUE_MONITORING"
        ) {
          setPendingConfirmation(null);
        }

        setFeedback(
          `${scenarioName}: ${reason ?? action ?? "Reading processed successfully."}`,
        );
      }

      await loadIncidents();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not submit simulation.",
      );
    } finally {
      setSimulating(false);
    }
  }

  async function sendWearerResponse(responseType: "SAFE" | "HELP") {
    const currentDevice = deviceId.trim();

    if (!currentDevice) {
      setError("Enter a device ID first.");
      return;
    }

    setSimulating(true);
    setError("");
    setFeedback("");

    try {
      const response = await fetch(`${API}/wearable/response`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          device_id: currentDevice,
          response: responseType,
        }),
      });

      const data: ApiResponse = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ??
            "Could not submit wearer response.",
        );
      }

      setPendingConfirmation(null);

      if (data.incident_id) {
        setFeedback(
          `HELP response received. Emergency incident created: ${data.incident_id}`,
        );
      } else {
        setFeedback(
          `${responseType} response processed: ${
            data.result?.reason ?? data.result?.action ?? "Success"
          }`,
        );
      }

      await loadIncidents();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not submit wearer response.",
      );
    } finally {
      setSimulating(false);
    }
  }

  async function updateStatus(status: string) {
    if (!selected) return;

    setUpdating(true);
    setError("");

    try {
      const response = await fetch(
        `${API}/incidents/${selected.incident_id}/status`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Status update failed.");
      }

      await loadIncidents();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not update incident.",
      );
    } finally {
      setUpdating(false);
    }
  }

  const demoScenarios = [
    {
      name: "Normal Movement",
      description: "Normal heart rate, no suspicious gesture.",
      className: "scenario-normal",
      reading: {
        heart_rate_bpm: 75,
        gesture_detected: false,
        ...DEMO_LOCATION,
      },
    },
    {
      name: "Suspicious Gesture",
      description: "Gesture detected; requests confirmation.",
      className: "scenario-warning",
      reading: {
        heart_rate_bpm: 85,
        gesture_detected: true,
        ...DEMO_LOCATION,
      },
    },
    {
      name: "High Heart Rate",
      description: "Elevated heart rate without a gesture.",
      className: "scenario-warning",
      reading: {
        heart_rate_bpm: 135,
        gesture_detected: false,
        ...DEMO_LOCATION,
      },
    },
    {
      name: "Gesture + High HR",
      description: "Gesture and elevated heart rate together.",
      className: "scenario-warning",
      reading: {
        heart_rate_bpm: 135,
        gesture_detected: true,
        ...DEMO_LOCATION,
      },
    },
    {
      name: "Trigger SOS",
      description: "Explicit SOS; immediate emergency escalation.",
      className: "scenario-danger",
      reading: {
        heart_rate_bpm: 80,
        gesture_detected: false,
        explicit_sos: true,
        ...DEMO_LOCATION,
      },
    },
    {
      name: "SOS Without GPS",
      description: "Explicit SOS with no location coordinates.",
      className: "scenario-danger",
      reading: {
        heart_rate_bpm: 80,
        gesture_detected: false,
        explicit_sos: true,
      },
    },
  ];

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">WEARABLE SAFETY SYSTEM</p>
          <h1>Emergency Command Center</h1>
          <p className="subtitle">
            Monitor incidents and manage simulated emergency responses.
          </p>
        </div>

        <div className="connection">
          <span
            className={`status-dot ${apiOnline ? "online" : "offline"}`}
          />
          <span>{apiOnline ? "API Connected" : "API Offline"}</span>
          <span className="simulation-tag">SIMULATION</span>
        </div>
      </header>

      <section className="simulation-banner">
        <strong>Prototype mode:</strong> All incidents and dispatch actions are
        simulated. No police department or emergency service is contacted.
      </section>

      {error && <div className="error-banner">{error}</div>}

      <section className="stats-grid">
        <article className="stat-card">
          <span>Total incidents</span>
          <strong>{incidents.length}</strong>
        </article>

        <article className="stat-card">
          <span>Emergency alerts</span>
          <strong className="red-text">{emergencyCount}</strong>
        </article>

        <article className="stat-card">
          <span>Open incidents</span>
          <strong>{openCount}</strong>
        </article>

        <article className="stat-card">
          <span>Active incidents</span>
          <strong>{activeCount}</strong>
        </article>
      </section>

      {/* SIMULATION CONTROLS */}
      <section className="panel simulator-panel">
        <div className="panel-heading">
          <div>
            <h2>Wearable Device Simulator</h2>
            <p>
              Generate synthetic sensor readings and test the backend alert
              workflow.
            </p>
          </div>

          <span className="simulation-tag">TEST ENVIRONMENT</span>
        </div>

        <div className="device-input-group">
          <label htmlFor="device-id">Wearable device ID</label>
          <input
            id="device-id"
            type="text"
            value={deviceId}
            onChange={(event) => setDeviceId(event.target.value)}
            placeholder="Enter device ID"
            disabled={simulating}
          />
          <span>
            Use different IDs to test independent wearable devices.
          </span>
        </div>

        <h3 className="simulator-subheading">Sensor scenarios</h3>

        <div className="scenario-grid">
          {demoScenarios.map((scenario) => (
            <article className="scenario-card" key={scenario.name}>
              <div>
                <h4>{scenario.name}</h4>
                <p>{scenario.description}</p>
              </div>

              <button
                className={`scenario-button ${scenario.className}`}
                disabled={simulating || !apiOnline}
                onClick={() =>
                  void submitReading(scenario.name, scenario.reading)
                }
              >
                {simulating ? "Processing..." : "Run scenario"}
              </button>
            </article>
          ))}
        </div>

        <div className="response-section">
          <div>
            <h3>Wearer confirmation</h3>
            <p>
              Respond to a pending suspicious event for the selected device.
            </p>
          </div>

          <div className="response-buttons">
            <button
              className="safe-button"
              disabled={simulating || !apiOnline || !hasPendingForDevice || secondsRemaining <= 0}
              onClick={() => void sendWearerResponse("SAFE")}
            >
              SAFE — Cancel alert
            </button>

            <button
              className="help-button"
              disabled={simulating || !apiOnline || !hasPendingForDevice || secondsRemaining <= 0}
              onClick={() => void sendWearerResponse("HELP")}
            >
              HELP — Escalate alert
            </button>
          </div>

          {pendingConfirmation && hasPendingForDevice ? (
            <div className="pending-alert">
              <div>
                <strong>Confirmation pending</strong>
                <p>
                  Device {pendingConfirmation.deviceId} must respond before
                  the timer expires.
                </p>
              </div>

              <strong className="countdown">
                {secondsRemaining}s
              </strong>
            </div>
          ) : (
            <p className="response-hint">
              No pending confirmation for this device.
            </p>
          )}
        </div>

        {feedback && (
          <div className="success-banner" role="status">
            {feedback}
          </div>
        )}

        <div className="simulator-note">
          <strong>Location note:</strong> Scenarios with GPS use sample
          coordinates (13.0827, 80.2707). These are test values, not a live
          wearable location. The SOS Without GPS scenario intentionally omits
          coordinates.
        </div>
      </section>

      {/* INCIDENT MANAGEMENT */}
      <section className="workspace">
        <section className="panel incident-panel">
          <div className="panel-heading">
            <div>
              <h2>Incident queue</h2>
              <p>Select an incident to inspect and manage it.</p>
            </div>

            <button
              className="secondary-button"
              onClick={() => void loadIncidents()}
            >
              Refresh
            </button>
          </div>

          <div className="filters">
            {statuses.map((status) => (
              <button
                key={status}
                className={`filter-button ${
                  filter === status ? "active" : ""
                }`}
                onClick={() => setFilter(status)}
              >
                {status === "DISPATCHED_SIMULATED" ? "DISPATCHED" : status}
              </button>
            ))}
          </div>

          {loading ? (
            <p className="empty-state">Loading incidents...</p>
          ) : visibleIncidents.length === 0 ? (
            <p className="empty-state">No incidents match this filter.</p>
          ) : (
            <div className="incident-list">
              {visibleIncidents.map((incident) => (
                <button
                  key={incident.incident_id}
                  className={`incident-row ${
                    selectedId === incident.incident_id ? "selected" : ""
                  }`}
                  onClick={() => setSelectedId(incident.incident_id)}
                >
                  <div className="incident-row-top">
                    <strong>{incident.device_id ?? "Unknown device"}</strong>

                    <span
                      className={`level-badge ${incident.alert_level.toLowerCase()}`}
                    >
                      {incident.alert_level}
                    </span>
                  </div>

                  <span className="incident-reason">
                    {incident.reason || "No reason provided"}
                  </span>

                  <div className="incident-row-bottom">
                    <span>{formatDate(incident.created_at)}</span>
                    <span className="status-label">{incident.status}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          <div className="panel-heading">
            <div>
              <h2>Incident details</h2>
              <p>Review the selected incident and update its status.</p>
            </div>
          </div>

          {!selected ? (
            <p className="empty-state">
              Select an incident from the queue.
            </p>
          ) : (
            <>
              <div className="detail-title">
                <span
                  className={`level-badge ${selected.alert_level.toLowerCase()}`}
                >
                  {selected.alert_level}
                </span>

                <h3>{selected.device_id ?? "Unknown device"}</h3>
                <p>{selected.reason || "No reason provided"}</p>
              </div>

              <dl className="detail-grid">
                <div>
                  <dt>Incident ID</dt>
                  <dd className="id-value">{selected.incident_id}</dd>
                </div>

                <div>
                  <dt>Created</dt>
                  <dd>{formatDate(selected.created_at)}</dd>
                </div>

                <div>
                  <dt>Heart rate</dt>
                  <dd>
                    {selected.heart_rate_bpm == null
                      ? "Unavailable"
                      : `${selected.heart_rate_bpm} BPM`}
                  </dd>
                </div>

                <div>
                  <dt>Incident status</dt>
                  <dd>{selected.status}</dd>
                </div>

                <div>
                  <dt>Delivery status</dt>
                  <dd>{selected.delivery_status}</dd>
                </div>

                <div>
                  <dt>GPS accuracy</dt>
                  <dd>
                    {selected.location_accuracy_m == null
                      ? "Unavailable"
                      : `${selected.location_accuracy_m} m`}
                  </dd>
                </div>

                <div>
                  <dt>Latitude</dt>
                  <dd>{selected.latitude ?? "Unavailable"}</dd>
                </div>

                <div>
                  <dt>Longitude</dt>
                  <dd>{selected.longitude ?? "Unavailable"}</dd>
                </div>
              </dl>

              {selected.latitude != null && selected.longitude != null && (
                <a
                  className="map-link"
                  href={`https://www.openstreetmap.org/?mlat=${selected.latitude}&mlon=${selected.longitude}#map=17/${selected.latitude}/${selected.longitude}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  View coordinates on OpenStreetMap ↗
                </a>
              )}

              <div className="action-section">
                <h3>Operator actions</h3>
                <p>
                  These controls update the local prototype database only.
                </p>

                <div className="action-buttons">
                  <button
                    className="primary-button"
                    disabled={updating || selected.status !== "OPEN"}
                    onClick={() => void updateStatus("ACKNOWLEDGED")}
                  >
                    Acknowledge
                  </button>

                  <button
                    className="warning-button"
                    disabled={
                      updating || selected.status !== "ACKNOWLEDGED"
                    }
                    onClick={() =>
                      void updateStatus("DISPATCHED_SIMULATED")
                    }
                  >
                    Simulate dispatch
                  </button>

                  <button
                    className="secondary-button"
                    disabled={updating || selected.status === "CLOSED"}
                    onClick={() => void updateStatus("CLOSED")}
                  >
                    Close incident
                  </button>
                </div>

                {updating && (
                  <p className="action-note">Updating status...</p>
                )}

                {selected.status === "DISPATCHED_SIMULATED" && (
                  <p className="action-note">
                    Simulated dispatch recorded. No real unit was contacted.
                  </p>
                )}

                {selected.status === "CLOSED" && (
                  <p className="action-note">This incident is closed.</p>
                )}
              </div>
            </>
          )}
        </section>
      </section>

      <footer>
        Wearable Silent Emergency Alert Band · Software prototype · No real
        emergency dispatch
      </footer>
    </main>
  );
}

export default App;