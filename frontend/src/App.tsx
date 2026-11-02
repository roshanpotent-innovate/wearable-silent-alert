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

const statuses = [
  "ALL",
  "OPEN",
  "ACKNOWLEDGED",
  "DISPATCHED_SIMULATED",
  "CLOSED",
];

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState("");

  const loadIncidents = useCallback(async () => {
    try {
      const response = await fetch(`${API}/incidents`);
      if (!response.ok) throw new Error("Could not load incidents.");

      const data: Incident[] = await response.json();
      setIncidents(data);
      setError("");

      setSelectedId((current) => {
        if (current && data.some((item) => item.incident_id === current)) {
          return current;
        }
        return data[0]?.incident_id ?? null;
      });
    } catch {
      setError("Backend unavailable. Check that the FastAPI server is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadIncidents();
    const timer = window.setInterval(() => void loadIncidents(), 3000);
    return () => window.clearInterval(timer);
  }, [loadIncidents]);

  const visibleIncidents =
    filter === "ALL"
      ? incidents
      : incidents.filter((incident) => incident.status === filter);

  const selected = incidents.find(
    (incident) => incident.incident_id === selectedId,
  );

  async function updateStatus(status: string) {
    if (!selected) return;

    setUpdating(true);
    setError("");

    try {
      const response = await fetch(
        `${API}/incidents/${selected.incident_id}/status`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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

  const openCount = incidents.filter((i) => i.status === "OPEN").length;
  const emergencyCount = incidents.filter(
    (i) => i.alert_level === "EMERGENCY",
  ).length;
  const activeCount = incidents.filter(
    (i) => i.status !== "CLOSED",
  ).length;

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
          <span className="status-dot" />
          <span>Local API</span>
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

      <section className="workspace">
        <section className="panel incident-panel">
          <div className="panel-heading">
            <div>
              <h2>Incident queue</h2>
              <p>Select an incident to inspect and manage it.</p>
            </div>
            <button className="secondary-button" onClick={() => void loadIncidents()}>
              Refresh
            </button>
          </div>

          <div className="filters">
            {statuses.map((status) => (
              <button
                key={status}
                className={`filter-button ${filter === status ? "active" : ""}`}
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
            <p className="empty-state">Select an incident from the queue.</p>
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
                <p>These controls update the local prototype database only.</p>

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
                      updating ||
                      selected.status !== "ACKNOWLEDGED"
                    }
                    onClick={() => void updateStatus("DISPATCHED_SIMULATED")}
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

                {updating && <p className="action-note">Updating status...</p>}
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