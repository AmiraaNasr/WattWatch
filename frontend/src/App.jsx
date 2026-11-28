import { useCallback, useEffect, useState } from "react";
import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import * as api from "./api.js";

const fmt = (iso) => new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });

function AnomalyDot({ cx, cy, payload }) {
  if (!payload.is_anomaly) return <g />;
  return <circle cx={cx} cy={cy} r={5} fill="#d1342f" stroke="#fff" strokeWidth={1.5} />;
}

export default function App() {
  const [readings, setReadings] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [stats, setStats] = useState({ total: 0, anomalies: 0, anomaly_rate: 0 });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    const [r, a, s] = await Promise.all([api.getReadings(), api.getAnomalies(), api.getStats()]);
    setReadings(r);
    setAnomalies(a);
    setStats(s);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setMessage(e.message));
  }, [refresh]);

  const run = (label, fn) => async (...args) => {
    setBusy(true);
    setMessage("");
    try {
      const res = await fn(...args);
      setMessage(`${label} : ${JSON.stringify(res)}`);
      await refresh();
    } catch (e) {
      setMessage(`Échec — ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const onFile = (e) => {
    const file = e.target.files[0];
    if (file) run("Import CSV", api.uploadCsv)(file);
    e.target.value = "";
  };

  return (
    <main className="page">
      <header>
        <h1>Consommation électrique</h1>
        <p>Repérez les pics et les coupures anormales avec une Isolation Forest.</p>
      </header>

      <section className="actions">
        <button disabled={busy} onClick={run("Données de démo chargées", api.loadDemo)}>
          Charger des données de démo
        </button>
        <label className={`button ${busy ? "disabled" : ""}`}>
          Importer un CSV (timestamp,kwh)
          <input type="file" accept=".csv" onChange={onFile} disabled={busy} hidden />
        </label>
        <button className="primary" disabled={busy || !stats.total} onClick={run("Analyse terminée", api.detect)}>
          Détecter les anomalies
        </button>
        <button className="ghost" disabled={busy || !stats.total} onClick={run("Données supprimées", api.resetData)}>
          Tout supprimer
        </button>
      </section>

      {message && <p className="message" role="status">{message}</p>}

      <section className="stats">
        <div><strong>{stats.total}</strong><span>mesures</span></div>
        <div className="alert"><strong>{stats.anomalies}</strong><span>anomalies</span></div>
        <div><strong>{(stats.anomaly_rate * 100).toFixed(1)} %</strong><span>du total</span></div>
      </section>

      <section className="chart">
        {readings.length === 0 ? (
          <p className="empty">Aucune mesure. Chargez les données de démo ou importez un CSV.</p>
        ) : (
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={readings} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#d9dee4" strokeDasharray="3 3" />
              <XAxis dataKey="ts" tickFormatter={fmt} minTickGap={60} fontSize={12} />
              <YAxis unit=" kWh" fontSize={12} width={70} />
              <Tooltip labelFormatter={fmt} formatter={(v) => [`${v} kWh`, "Consommation"]} />
              <Line type="monotone" dataKey="kwh" stroke="#1f6f8b" strokeWidth={1.6} dot={<AnomalyDot />} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </section>

      <section>
        <h2>Anomalies détectées</h2>
        {anomalies.length === 0 ? (
          <p className="empty">Aucune anomalie pour le moment.</p>
        ) : (
          <table>
            <thead>
              <tr><th>Date</th><th>kWh</th><th>Score</th></tr>
            </thead>
            <tbody>
              {anomalies.map((a) => (
                <tr key={a.id}>
                  <td>{fmt(a.ts)}</td>
                  <td>{a.kwh.toFixed(2)}</td>
                  <td>{a.score?.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
