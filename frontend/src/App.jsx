import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Dashboard from "./pages/Dashboard";
import "./App.css";

function App() {
  return (
    <div className="app">

      <Sidebar />

      <main className="main-content">

        <Topbar />

        <Dashboard />

      </main>

    </div>
  );
}

export default App;