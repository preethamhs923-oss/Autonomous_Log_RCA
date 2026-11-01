
import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Dashboard from "./pages/Dashboard";
import ModulePage from "./pages/ModulePage";
import Login from "./pages/Login";
import "./App.css";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activePage, setActivePage] = useState("Dashboard");
  const [searchTerm, setSearchTerm] = useState("");
  const [refreshToken, setRefreshToken] = useState(0);

  const handleRefresh = () => {
    setRefreshToken((previous) => previous + 1);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setActivePage("Dashboard");
    setSearchTerm("");
  };

  if (!isLoggedIn) {
    return <Login onLogin={() => setIsLoggedIn(true)} />;
  }

  return (
    <div className="app">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
      />

      <main className="main-content">
        <div className="app-topbar-row">
          <Topbar
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            onRefresh={handleRefresh}
          />
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>

        {activePage === "Dashboard" ? (
          <Dashboard
            refreshToken={refreshToken}
            searchTerm={searchTerm}
          />
        ) : (
          <ModulePage
            page={activePage}
            searchTerm={searchTerm}
            refreshToken={refreshToken}
          />
        )}
      </main>
    </div>
  );
}

export default App;
