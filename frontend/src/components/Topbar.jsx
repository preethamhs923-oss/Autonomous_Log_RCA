
import {
  Bell,
  Search,
  RefreshCw,
  CircleUserRound,
} from "lucide-react";

function Topbar({ searchTerm, onSearchChange, onRefresh }) {
  return (
    <header className="topbar">
      <div className="search-box">
        <Search size={18} />

        <input
          type="search"
          value={searchTerm}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search logs, incidents, services..."
          aria-label="Search dashboard data"
        />
      </div>

      <div className="topbar-actions">
        <button
          type="button"
          className="icon-button"
          onClick={onRefresh}
          title="Refresh data"
          aria-label="Refresh data"
        >
          <RefreshCw size={18} />
        </button>

        <button
          type="button"
          className="icon-button notification"
          title="Notifications"
          aria-label="Notifications"
          onClick={() =>
            window.alert("Notifications are not connected yet.")
          }
        >
          <Bell size={18} />
          <span />
        </button>

        <div className="user-profile">
          <CircleUserRound size={28} />
          <div>
            <strong>Administrator</strong>
            <small>System Operator</small>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Topbar;
