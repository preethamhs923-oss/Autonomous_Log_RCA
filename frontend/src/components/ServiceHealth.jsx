function ServiceHealth({ services = [] }) {
  return (
    <div className="service-health-card">
      <div className="section-header">
        <div>
          <h2>Service Health</h2>
          <p>Real-time health status of monitored services</p>
        </div>
      </div>

      <div className="service-list">
        {services.length === 0 ? (
          <div className="empty-state">
            <p>No service data available</p>
            <span>Waiting for backend telemetry.</span>
          </div>
        ) : (
          services.map((service, index) => {
            const name =
              typeof service === "string"
                ? service
                : service.service || service.name || `Service ${index + 1}`;

            const status =
              typeof service === "string"
                ? "HEALTHY"
                : service.status || service.health || "HEALTHY";

            const normalizedStatus = String(status).toUpperCase();

            return (
              <div className="service-row" key={name + index}>
                <div className="service-info">
                  <span className="service-indicator"></span>

                  <div className="service-details">
                    <strong>{name}</strong>
                    <small>Monitored service</small>
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