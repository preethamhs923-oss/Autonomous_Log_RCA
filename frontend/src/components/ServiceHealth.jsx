
function ServiceHealth({ services = {} }) {
  // Convert the backend object into an array for React
  const serviceList = Array.isArray(services)
    ? services
    : Object.entries(services || {}).map(([service, details]) => ({
        service,
        ...details,
      }));

  return (
    <div className="service-health-card">
      <div className="service-list">
        {serviceList.length === 0 ? (
          <div className="empty-state">
            <p>No service data available</p>
            <span>Waiting for backend telemetry.</span>
          </div>
        ) : (
          serviceList.map((service, index) => {
            const rawName =
              service.service || service.name || `Service ${index + 1}`;

            const name = rawName
              .replace(/-/g, " ")
              .replace(/\b\w/g, (char) => char.toUpperCase());

            const status = service.status || service.health || "HEALTHY";
            const normalizedStatus = String(status).toUpperCase();

            const total = service.total ?? 0;
            const anomalies = service.anomalies ?? 0;

            return (
              <div className="service-row" key={rawName + index}>
                <div className="service-info">
                  <span
                    className={`service-indicator ${normalizedStatus.toLowerCase()}`}
                  ></span>

                  <div className="service-details">
                    <strong>{name}</strong>
                    <small>
                      {anomalies} anomalies / {total} total logs
                    </small>
                  </div>
                </div>

                <span
                  className={`service-status ${normalizedStatus.toLowerCase()}`}
                >
                  {normalizedStatus}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default ServiceHealth;
