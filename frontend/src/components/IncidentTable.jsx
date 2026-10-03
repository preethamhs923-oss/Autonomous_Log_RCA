function IncidentTable({ incidents = [] }) {
  return (
    <div className="incident-table-card">
      <div className="section-header">
        <div>
          <h2>Recent Incidents</h2>
          <p>Latest detected anomalies and system events</p>
        </div>
      </div>

      <div className="table-container">
        {incidents.length === 0 ? (
          <div className="empty-state">
            <p>No incidents detected</p>
            <span>System is currently operating normally.</span>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Service</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Message</th>
              </tr>
            </thead>

            <tbody>
              {incidents.map((incident, index) => (
                <tr key={incident.trace_id || index}>
                  <td>{incident.timestamp || "-"}</td>

                  <td>
                    <span className="service-name">
                      {incident.service || "-"}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`severity ${(
                        incident.severity || "NORMAL"
                      ).toLowerCase()}`}
                    >
                      {incident.severity || "NORMAL"}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`status ${(
                        incident.final_status || "NORMAL"
                      ).toLowerCase()}`}
                    >
                      {incident.final_status || "NORMAL"}
                    </span>
                  </td>

                  <td className="message-cell">
                    {incident.message || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default IncidentTable;