import { useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/health`)
      .then((res) => res.json())
      .then((data) => setStatus(`Backend says: ${data.status}`))
      .catch((err) => setStatus(`Error reaching backend: ${err.message}`));
  }, []);

  return (
    <div style={{ padding: 40, fontFamily: "sans-serif" }}>
      <h1>Weather-Aware Truck Routing — Skeleton</h1>
      <p>{status}</p>
    </div>
  );
}

export default App;
