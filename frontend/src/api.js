// src/api.js
const API_BASE =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  (typeof process !== "undefined" && process.env?.REACT_APP_API_URL) ||
  "https://growth-99-graph-production.up.railway.app"; // FIX: Use correct Railway URL

export async function sendQuery({
  session_id,
  text,
  llm_model = "gpt-4o",
  file = null,
  logo = null,
  image = null,
  color_palette = "",
  regenerate = false,
  schema_type = "medspa"  // Add schema_type parameter
}) {
  const formData = new FormData();
  
  if (session_id) formData.append("session_id", session_id);
  formData.append("text", text);
  formData.append("llm_model", llm_model);
  formData.append("color_palette", color_palette);
  formData.append("regenerate", regenerate.toString());
  formData.append("schema_type", schema_type);  // Add schema_type to form data
  
  if (file) formData.append("file", file);
  if (logo) formData.append("logo", logo);
  if (image) formData.append("image", image);

  // FIX: Ensure no double slashes
  const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/query`;
  const res = await fetch(apiUrl, { method: "POST", body: formData });
  
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg || "Request failed");
  }
  return res.json();
}

export async function downloadProjectFiles(conversationId) {
  const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/conversations/${conversationId}/download`;
  const res = await fetch(apiUrl, { method: "GET" });
  
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg || "Download failed");
  }
  
  return res.blob();
}