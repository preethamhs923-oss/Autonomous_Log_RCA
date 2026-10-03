import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Server,
} from "lucide-react";

function StatCard({
  title = "Metric",
  value = 0,
  subtitle = "",
  type = "default",
}) {
  const icons = {
    logs: Activity,
    anomalies: AlertTriangle,
    services: Server,
    healthy: CheckCircle,
    default: Activity,
  };

  const Icon = icons[type] || Activity;

  return (
    <div className={`stat-card stat-${type}`}>
      <div className="stat-card-top">
        <div className="stat-icon">
          <Icon size={22} />
        </div>

        <span className="stat-label">{title}</span>
      </div>

      <div className="stat-value">
        {value}
      </div>

      {subtitle && (
        <div className="stat-subtitle">
          {subtitle}
        </div>
      )}
    </div>
  );
}

export default StatCard;