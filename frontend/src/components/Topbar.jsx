import {
  Bell,
  Search,
  RefreshCw,
  CircleUserRound,
} from "lucide-react";

function Topbar() {
  return (
    <header className="topbar">

      <div className="search-box">
        <Search size={18} />
        <input
          type="text"
          placeholder="Search logs, incidents, services..."
        />
      </div>

      <div className="topbar-actions">

        <button className="icon-button">
          <RefreshCw size={18} />
        </button>

        <button className="icon-button notification">
          <Bell size={18} />
          <span></span>
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