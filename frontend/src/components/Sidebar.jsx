
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Network,
  Search,
  Brain,
  Settings,
  Server,
  ShieldCheck,
  ChevronRight,
} from "lucide-react";

function Sidebar({ activePage, onNavigate }) {
  const menuItems = [
    {
      section: "MONITORING",
      items: [
        { name: "Dashboard", icon: LayoutDashboard },
        { name: "Log Analytics", icon: Activity },
        { name: "Anomalies", icon: AlertTriangle },
        { name: "Services", icon: Server },
      ],
    },
    {
      section: "INTELLIGENCE",
      items: [
        { name: "Incidents", icon: Network },
        { name: "Root Cause", icon: Search },
        { name: "AI Intelligence", icon: Brain },
      ],
    },
    {
      section: "SYSTEM",
      items: [
        { name: "Security", icon: ShieldCheck },
        { name: "Settings", icon: Settings },
      ],
    },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <Brain size={22} />
        </div>

        <div className="logo-text">
          <h2>LogRCA</h2>
          <span>Autonomous Intelligence</span>
        </div>
      </div>

      <div className="system-status">
        <span className="status-indicator" />
        <div>
          <span className="status-label">SYSTEM STATUS</span>
          <strong>Operational</strong>
        </div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((section) => (
          <div className="nav-section" key={section.section}>
            <div className="nav-section-title">
              {section.section}
            </div>

            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.name;

              return (
                <button
                  type="button"
                  className={`nav-item ${isActive ? "active" : ""}`}
                  key={item.name}
                  onClick={() => onNavigate(item.name)}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon size={18} />
                  <span>{item.name}</span>

                  {isActive && (
                    <ChevronRight size={15} className="nav-arrow" />
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="pipeline-info">
          <span>PIPELINE</span>
          <strong>v1.0.0</strong>
        </div>

        <div className="environment-info">
          <span>ENVIRONMENT</span>
          <strong>LOCAL</strong>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
