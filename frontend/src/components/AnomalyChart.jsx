import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function AnomalyChart({ data = [] }) {

  console.log("AnomalyChart received data:", data);

  if (!data || data.length === 0) {
    return (
      <div className="anomaly-chart-empty">
        <h3>Anomaly Detection</h3>

        <p>Real-time anomaly score analysis</p>

        <p>
          <span>●</span> Live Analysis
        </p>

        <p>No anomaly data available</p>
      </div>
    );
  }

  return (
    <div className="anomaly-chart">

      <div className="chart-header">
        <h3>Anomaly Detection</h3>

        <p>Real-time anomaly score analysis</p>
      </div>

      <ResponsiveContainer width="100%" height={300}>

        <LineChart data={data}>

          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => {
              if (!value) return "";
              return value.substring(11, 16);
            }}
          />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="anomaly_score"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={false}
          />

        </LineChart>

      </ResponsiveContainer>

    </div>
  );
}

export default AnomalyChart;