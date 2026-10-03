import { useEffect, useState } from "react";
import axios from "axios";

import StatCard from "../components/StatCard";
import AnomalyChart from "../components/AnomalyChart";
import ServiceHealth from "../components/ServiceHealth";
import IncidentTable from "../components/IncidentTable";

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(
        "http://127.0.0.1:5000/api/dashboard"
      );

      console.log("Dashboard API data:", response.data);

      setDashboardData(response.data);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <h2>Loading dashboard...</h2>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="dashboard">
        <h2>Unable to load dashboard data</h2>
        <p>Make sure the Flask backend is running on port 5000.</p>
      </div>
    );
  }

  const logs = dashboardData.all_logs || [];

  /*
   * Prepare anomaly data for the chart.
   *
   * We take the latest 100 logs so the chart
   * remains fast and readable.
   */
  const anomalyData = logs.slice(-100).map((log) => ({
    timestamp: log.timestamp,
    anomaly_score: Number(log.anomaly_score || 0),
    status: log.status,
    final_status: log.final_status,
  }));

  const totalLogs = logs.length;

  const anomalies = logs.filter(
    (log) => log.status === "ANOMALY"
  ).length;

  const criticalEvents = logs.filter(
    (log) => log.severity === "CRITICAL"
  ).length;

  const services = new Set(
    logs.map((log) => log.service)
  ).size;
  // Prepare service health data
const serviceMap = {};

logs.forEach((log) => {
  const serviceName = log.service || "unknown";

  if (!serviceMap[serviceName]) {
    serviceMap[serviceName] = {
      service: serviceName,
      total: 0,
      anomalies: 0,
      critical: 0,
    };
  }

  serviceMap[serviceName].total += 1;

  if (
    log.status === "ANOMALY" ||
    log.final_status === "ANOMALY"
  ) {
    serviceMap[serviceName].anomalies += 1;
  }

  if (log.severity === "CRITICAL") {
    serviceMap[serviceName].critical += 1;
  }
});

const serviceHealthData = Object.values(serviceMap).map((service) => {
  let status = "HEALTHY";

  if (service.critical > 0) {
    status = "CRITICAL";
  } else if (service.anomalies > 0) {
    status = "DEGRADED";
  }

  return {
    ...service,
    status,
  };
});

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
          value={anomalies}
          subtitle="Detected events"
        />

        <StatCard
          title="Critical Events"
          value={criticalEvents}
          subtitle="Require attention"
        />

        <StatCard
          title="Services"
          value={services}
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
              <span>Detection trend</span>
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


      {/* INCIDENT TABLE */}
      <section className="panel incident-panel">

        <div className="panel-header">

          <div>
            <h2>Recent Incidents</h2>
            <span>Latest detected events</span>
          </div>

        </div>

        <IncidentTable
  incidents={logs
    .filter((log) => log.status === "ANOMALY")
    .slice(-10)
    .reverse()}
/>

      </section>

    </div>
  );
}

export default Dashboard;