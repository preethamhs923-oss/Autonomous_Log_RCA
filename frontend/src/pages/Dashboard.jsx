
import { useEffect, useState } from "react";
import { getDashboardData } from "../services/api";

import StatCard from "../components/StatCard";
import AnomalyChart from "../components/AnomalyChart";
import ServiceHealth from "../components/ServiceHealth";
import IncidentTable from "../components/IncidentTable";

function Dashboard({ refreshToken, searchTerm = "" }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await getDashboardData();

        if (isMounted) {
          setDashboardData(response);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);

        if (isMounted) {
          setError("Unable to connect to the backend.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchDashboardData();

    return () => {
      isMounted = false;
    };
  }, [refreshToken]);

  if (loading) {
    return (
      <div className="dashboard">
        <h2>Loading dashboard...</h2>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="dashboard">
        <h2>Unable to load dashboard data</h2>
        <p>{error || "No dashboard data received."}</p>
      </div>
    );
  }

  // Backend response sections
  const summary = dashboardData.summary || {};
  const logs = dashboardData.all_logs || [];
  const anomalies = dashboardData.recent_anomalies || [];
  const backendServices = dashboardData.services || {};

  // Search filtering
  const query = searchTerm.trim().toLowerCase();

  const matchesSearch = (item) => {
    if (!query) return true;

    return [
      item.message,
      item.service,
      item.level,
      item.status,
      item.final_status,
      item.severity,
    ].some((value) =>
      String(value ?? "").toLowerCase().includes(query)
    );
  };

  const filteredLogs = logs.filter(matchesSearch);

  const filteredAnomalies = anomalies.filter(matchesSearch);

  // Anomaly chart data
  const anomalyData = filteredAnomalies.map((item) => ({
    timestamp: item.timestamp,
    anomaly_score: Number(item.anomaly_score || 0),
    status: item.status || "ANOMALY",
    final_status: item.final_status || item.status || "ANOMALY",
  }));

  // Convert backend service object into the array
  // expected by ServiceHealth.jsx
  const serviceHealthData = Object.entries(backendServices).map(
  ([serviceName, details]) => ({
    service: serviceName,
    total: details.total || 0,
    anomalies: details.anomalies || 0,
    status:
      details.status ||
      (details.anomalies > 0 ? "DEGRADED" : "HEALTHY"),
  })
);


  // Normalize incident records for IncidentTable.jsx
  const incidentData = filteredAnomalies
    .map((item) => ({
      ...item,
      timestamp: item.timestamp || "-",
      service: item.service || "unknown",
      severity: item.severity || item.level || "UNKNOWN",
      status: item.status || "ANOMALY",
      final_status:
        item.final_status || item.status || "ANOMALY",
      message: item.message || item.explanation || "-",
    }))
    .slice(-10)
    .reverse();

  const totalLogs = summary.total_logs ?? logs.length;
  const totalAnomalies = summary.anomalies ?? anomalies.length;
  const criticalEvents = summary.critical ?? 0;
  const totalServices = Object.keys(backendServices).length;

  return (
    <div className="dashboard">

      {/* PAGE HEADER */}
      <div className="page-header">
        <div>
          <h1>System Overview</h1>
          <p>
            Autonomous monitoring, anomaly detection and root cause analysis
          </p>
        </div>

        <div className="live-status">
          <span></span>
          LIVE MONITORING
        </div>
      </div>

      {/* STATISTICS */}
      <section className="stats-grid">
        <StatCard
          title="Total Logs"
          value={totalLogs}
          subtitle="Processed events"
        />

        <StatCard
          title="Anomalies"
          value={totalAnomalies}
          subtitle="Detected events"
        />

        <StatCard
          title="Critical Events"
          value={criticalEvents}
          subtitle="Require attention"
        />

        <StatCard
          title="Services"
          value={totalServices}
          subtitle="Monitored services"
        />
      </section>

      {/* DASHBOARD GRID */}
      <section className="dashboard-grid">

        {/* ANOMALY CHART */}
        <div className="panel large-panel">
          <div className="panel-header">
            <div>
              <h2>Anomaly Activity</h2>
              <span>Recent detection trend</span>
            </div>
          </div>

          <AnomalyChart data={anomalyData} />
        </div>

        {/* SERVICE HEALTH */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <h2>Service Health</h2>
              <span>Current status</span>
            </div>
          </div>

          <ServiceHealth services={serviceHealthData} />
        </div>

      </section>

      {/* RECENT INCIDENTS */}
      <section className="panel incident-panel">
        <div className="panel-header">
          <div>
            <h2>Recent Incidents</h2>
            <span>Latest detected anomalies</span>
          </div>
        </div>

        <IncidentTable incidents={incidentData} />
      </section>

    </div>
  );
}

export default Dashboard;
