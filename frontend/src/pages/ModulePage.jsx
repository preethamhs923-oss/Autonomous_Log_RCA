
import { useEffect, useMemo, useState } from "react";
import api, { getDashboardData } from "../services/api";

const descriptions = {
  "Log Analytics": "Browse and search ingested application logs.",
  Anomalies: "Review events identified by the detection pipeline.",
  Services: "Review activity grouped by monitored service.",
  Incidents: "View incident records stored in PostgreSQL.",
  "Root Cause": "Explore root-cause explanations and confidence values.",
  "AI Intelligence": "Review AI analysis and code recommendations.",
  Security: "Review suspicious events and their severity.",
  Settings: "Local application and backend connection information.",
};

const endpoints = {
  Incidents: "/incidents",
  "Root Cause": "/root-causes",
  "AI Intelligence": "/ai-intelligence",
  Security: "/security",
};

function extractRecords(payload, preferredKeys = []) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];

  for (const key of preferredKeys) {
    if (Array.isArray(payload[key])) return payload[key];
  }

  const arrays = Object.values(payload).filter(Array.isArray);

  if (arrays.length === 1) return arrays[0];
  if (arrays.length === 0) return [payload];

  return arrays.flat();
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";

  if (typeof value === "object") return JSON.stringify(value);

  return String(value);
}

function readNested(value) {
  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return {};
    }
  }

  return value && typeof value === "object" ? value : {};
}

function getIncidentValue(record, key) {
  const details = readNested(record.incident_data);
  const nestedIncident = readNested(details.incident);
  const result = readNested(record.result_data);

  const values = {
    incident_id:
      record.incident_id ?? record.id ?? result.incident_id,
    incident_key:
      record.incident_key ??
      details.incident_key ??
      nestedIncident.incident_key ??
      result.incident_key,
    service:
      record.service_name ??
      record.service ??
      details.service ??
      nestedIncident.service ??
      result.service,
    severity:
      record.severity ??
      details.severity ??
      nestedIncident.severity ??
      result.severity,
    event_count:
      record.event_count ??
      details.event_count ??
      nestedIncident.event_count ??
      (Array.isArray(details.events) ? details.events.length : undefined),
    first_seen:
      record.first_seen ??
      record.start_time ??
      details.first_seen ??
      details.start_time,
    last_seen:
      record.last_seen ??
      record.end_time ??
      details.last_seen ??
      details.end_time,
  };

  return values[key];
}

function getRootCauseValue(record, key) {
  const result = readNested(record.result_data);
  const details = readNested(record.incident_data);
  const intelligence = readNested(details.intelligence);

  const values = {
    incident_id:
      record.incident_id ??
      record.id ??
      result.incident_id ??
      intelligence.incident_id,

    root_cause:
      record.root_cause ??
      result.root_cause ??
      intelligence.root_cause ??
      details.root_cause,

    confidence:
      record.confidence ??
      result.confidence ??
      intelligence.confidence ??
      details.confidence,

    explanation:
      record.explanation ??
      record.description ??
      result.explanation ??
      result.description ??
      intelligence.recommended_action ??
      intelligence.explanation ??
      details.explanation,
  };

  return values[key];
}

function formatConfidence(value) {
  if (value === null || value === undefined || value === "") return "—";

  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);

  return `${(number <= 1 ? number * 100 : number).toFixed(1)}%`;
}

function RecordsTable({
  title,
  records,
  searchTerm,
  columns,
  getValue,
}) {
  const filtered = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    if (!query) return records;

    return records.filter((record) =>
      Object.values(record || {}).some((value) =>
        formatValue(value).toLowerCase().includes(query)
      )
    );
  }, [records, searchTerm]);

  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          <span>{filtered.length} records</span>
        </div>
      </div>

      <div className="module-table-wrap">
        <table className="module-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column.key}>{column.label}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {filtered.slice(0, 200).map((record, index) => (
              <tr key={record.id ?? record.incident_id ?? index}>
                {columns.map((column) => {
                  const value = getValue(record, column.key);

                  return (
                    <td key={column.key} title={formatValue(value)}>
                      {column.key === "confidence"
                        ? formatConfidence(value)
                        : formatValue(value)}
                    </td>
                  );
                })}
              </tr>
            ))}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={columns.length}>
                  No matching records found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {filtered.length > 200 && (
        <div className="module-details">
          Showing the first 200 matching records. Use search to find others.
        </div>
      )}
    </div>
  );
}

function ModulePage({ page, searchTerm = "", refreshToken }) {
  const [data, setData] = useState(null);
  const [moduleData, setModuleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError("");

      try {
        const dashboardPromise = getDashboardData();
        const endpoint = endpoints[page];

        const modulePromise = endpoint
          ? api.get(endpoint).then((response) => response.data)
          : Promise.resolve(null);

        const [dashboard, result] = await Promise.all([
          dashboardPromise,
          modulePromise,
        ]);

        if (!cancelled) {
          setData(dashboard);
          setModuleData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.error ||
              `Could not load ${page} data. Check the Flask backend and API endpoint.`
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadData();

    return () => {
      cancelled = true;
    };
  }, [page, refreshToken]);

  const logs = data?.all_logs || [];
  const anomalies = data?.recent_anomalies || [];

  const services = useMemo(
    () =>
      Object.entries(data?.services || {}).map(([name, stats]) => ({
        name,
        ...stats,
      })),
    [data]
  );

  const incidents = useMemo(
    () =>
      extractRecords(moduleData, [
        "incidents",
        "records",
        "data",
        "results",
      ]),
    [moduleData]
  );

  const rootCauses = useMemo(
    () =>
      extractRecords(moduleData, [
        "root_cause_results",
        "root_causes",
        "results",
        "records",
        "data",
      ]),
    [moduleData]
  );

  const intelligenceRecords = useMemo(() => {
    if (!moduleData) return [];

    if (Array.isArray(moduleData)) return moduleData;

    const code = extractRecords(moduleData.code_analysis_results ?? moduleData.code_analysis);
    const recommendations = extractRecords(
      moduleData.refactoring_recommendations ?? moduleData.recommendations
    );

    if (code.length || recommendations.length) {
      return [
        ...code.map((item) => ({ ...item, result_type: "Code Analysis" })),
        ...recommendations.map((item) => ({
          ...item,
          result_type: "Refactoring Recommendation",
        })),
      ];
    }

    return extractRecords(moduleData, ["records", "results", "data"]);
  }, [moduleData]);

  const filteredLogs = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    const matches = (item) =>
      !query ||
      [
        item.message,
        item.service,
        item.level,
        item.status,
        item.final_status,
        item.severity,
        item.source_ip,
      ].some((value) =>
        String(value ?? "").toLowerCase().includes(query)
      );

    if (page === "Anomalies" || page === "Security") {
      return anomalies.filter(matches);
    }

    return logs.filter(matches);
  }, [logs, anomalies, page, searchTerm]);

  if (loading) {
    return (
      <section className="dashboard">
        <h1>{page}</h1>
        <p>Loading data from PostgreSQL...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="dashboard">
        <h1>{page}</h1>
        <p role="alert">{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="dashboard">
        <h1>{page}</h1>
        <p>No dashboard data is available.</p>
      </section>
    );
  }

  return (
    <section className="dashboard">
      <div className="page-header">
        <div>
          <h1>{page}</h1>
          <p>{descriptions[page] || "Project information"}</p>
        </div>

        <div className="live-status">
          <span />
          API CONNECTED
        </div>
      </div>

      {page === "Incidents" ? (
        <RecordsTable
          title="Incident Overview"
          records={incidents}
          searchTerm={searchTerm}
          getValue={getIncidentValue}
          columns={[
            { key: "incident_id", label: "Incident ID" },
            { key: "incident_key", label: "Incident Key" },
            { key: "service", label: "Service" },
            { key: "severity", label: "Severity" },
            { key: "event_count", label: "Events" },
            { key: "first_seen", label: "First Seen" },
            { key: "last_seen", label: "Last Seen" },
          ]}
        />
      ) : page === "Root Cause" ? (
        <RecordsTable
          title="Root Cause Analysis"
          records={rootCauses}
          searchTerm={searchTerm}
          getValue={getRootCauseValue}
          columns={[
            { key: "incident_id", label: "Incident ID" },
            { key: "root_cause", label: "Root Cause" },
            { key: "confidence", label: "Confidence" },
            { key: "explanation", label: "Explanation" },
          ]}
        />
      ) : page === "AI Intelligence" ? (
        <RecordsTable
          title="AI Intelligence Results"
          records={intelligenceRecords}
          searchTerm={searchTerm}
          getValue={(record, key) => record[key]}
          columns={[
            { key: "result_type", label: "Result Type" },
            { key: "id", label: "ID" },
            { key: "service", label: "Service" },
            { key: "file", label: "File" },
            { key: "recommendation", label: "Recommendation" },
            { key: "description", label: "Description" },
          ]}
        />
      ) : page === "Services" ? (
        <div className="panel">
          <div className="panel-header">
            <h2>Service Activity</h2>
          </div>

          <div className="module-table-wrap">
            <table className="module-table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Total Logs</th>
                  <th>Anomalies</th>
                </tr>
              </thead>
              <tbody>
                {services.map((service) => (
                  <tr key={service.name}>
                    <td>{service.name}</td>
                    <td>{service.total}</td>
                    <td>{service.anomalies}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : page === "Settings" ? (
        <div className="panel">
          <div className="panel-header">
            <h2>Application Settings</h2>
          </div>
          <div className="module-details">
            <p><strong>Backend:</strong> Flask</p>
            <p><strong>Database:</strong> PostgreSQL</p>
            <p><strong>API:</strong> http://127.0.0.1:5000/api</p>
            <p><strong>Total logs:</strong> {logs.length}</p>
          </div>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2>
                {page === "Log Analytics"
                  ? "Application Logs"
                  : page === "Security"
                  ? "Security Events"
                  : "Detected Anomalies"}
              </h2>
              <span>{filteredLogs.length} matching records</span>
            </div>
          </div>

          <div className="module-table-wrap">
            <table className="module-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Service</th>
                  <th>Level</th>
                  <th>Message</th>
                  <th>Status</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.slice(-200).reverse().map((item, index) => (
                  <tr key={item.id ?? item.source_key ?? index}>
                    <td>{item.timestamp || "—"}</td>
                    <td>{item.service || "unknown"}</td>
                    <td>{item.level || "—"}</td>
                    <td>{item.message || "—"}</td>
                    <td>{item.final_status || item.status || "—"}</td>
                    <td>{item.severity || "—"}</td>
                  </tr>
                ))}

                {filteredLogs.length === 0 && (
                  <tr>
                    <td colSpan="6">No matching records found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

export default ModulePage;
