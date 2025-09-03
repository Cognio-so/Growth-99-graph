// src/api.js
const API_BASE =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  (typeof process !== "undefined" && process.env?.REACT_APP_API_URL) ||
  "https://your-railway-url.railway.app"; // Update this line

export async function sendQuery({ session_id, text, llm_model, file, regenerate }) {
  const form = new FormData();
  if (session_id) form.append("session_id", session_id);
  form.append("text", text);
  if (llm_model) form.append("llm_model", llm_model);
  if (file) form.append("file", file, file.name);
  if (typeof regenerate !== "undefined") form.append("regenerate", String(!!regenerate));

  // FIX: Ensure no double slashes
  const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/query`;
  const res = await fetch(apiUrl, { method: "POST", body: form });
  
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg || "Request failed");
  }
  return res.json();
}