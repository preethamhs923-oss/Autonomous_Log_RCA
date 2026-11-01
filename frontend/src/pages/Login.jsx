
import { useState } from "react";

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    // Temporary frontend-only demo login.
    // We will replace this with Flask authentication next.
    if (
      email.trim().toLowerCase() === "admin@example.com" &&
      password === "Demo@123"
    ) {
      onLogin();
    } else {
      setError("Invalid credentials. Please try again.");
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <div className="login-logo">AI</div>
          <div>
            <h1>virtualvortex AI</h1>
            <p>Autonomous Log Root Cause Analysis</p>
          </div>
        </div>

        <div className="login-heading">
          <h2>Welcome back</h2>
          <p>Sign in to access your monitoring dashboard.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="login-email">Email address</label>
          <input
            id="login-email"
            type="email"
            placeholder="admin@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="username"
            required
          />

          <label htmlFor="login-password">Password</label>
          <div className="password-field">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              className="show-password"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-submit">
            Sign in to dashboard
          </button>
        </form>

        <p className="login-footer">
          AI-powered monitoring · Incident investigation · Root cause analysis
        </p>
      </div>
    </div>
  );
}

export default Login;
