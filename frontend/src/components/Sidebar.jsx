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

function Sidebar() {
  const menuItems = [
    {
      section: "MONITORING",
      items: [
        {
          name: "Dashboard",
          icon: LayoutDashboard,
          active: true,
        },
        {
          name: "Log Analytics",
          icon: Activity,
        },
        {
          name: "Anomalies",
          icon: AlertTriangle,
        },
        {
          name: "Services",
          icon: Server,
        },
      ],
    },
    {
      section: "INTELLIGENCE",
      items: [
        {
          name: "Incidents",
          icon: Network,
        },
        {
          name: "Root Cause",
          icon: Search,
        },
        {
          name: "AI Intelligence",
          icon: Brain,
        },
      ],
    },
    {
      section: "SYSTEM",
      items: [
        {
          name: "Security",
          icon: ShieldCheck,
        },
        {
          name: "Settings",
          icon: Settings,
        },
      ],
    },
  ];

  return (
    <aside className="sidebar">

      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-mark">
          <Brain size={22} />
        </div>

        <div className="logo-text">
          <h2>LogRCA</h2>
          <span>Autonomous Intelligence</span>
        </div>
      </div>

      {/* System Status */}
      <div className="system-status">
        <span className="status-indicator"></span>

        <div>
          <span className="status-label">SYSTEM STATUS</span>
          <strong>Operational</strong>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">

        {menuItems.map((section) => (
          <div className="nav-section" key={section.section}>

            <div className="nav-section-title">
              {section.section}
            </div>

            {section.items.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  className={`nav-item ${
                    item.active ? "active" : ""
                  }`}
                  key={item.name}
                >
                  <Icon size={18} />

                  <span>{item.name}</span>

                  {item.active && (
                    <ChevronRight
                      size={15}
                      className="nav-arrow"
                    />
                  )}
                </button>
              );
            })}

          </div>
        ))}

      </nav>

      {/* Bottom System Information */}
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