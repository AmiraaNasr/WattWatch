const BASE = import.meta.env.VITE_API_URL || "/api";

async function call(path, options) {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

export const getReadings = () => call("/readings?limit=2000");
export const getAnomalies = () => call("/anomalies");
export const getStats = () => call("/stats");
export const loadDemo = () => call("/demo", { method: "POST" });
export const detect = () => call("/detect", { method: "POST" });
export const resetData = () => call("/readings", { method: "DELETE" });

export const uploadCsv = (file) => {
  const form = new FormData();
  form.append("file", file);
  return call("/readings/upload", { method: "POST", body: form });
};
