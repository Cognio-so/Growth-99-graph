import { useState } from "react";

export default function UserQueryForm() {
  const [form, setForm] = useState({
    project_id: "",
    user_id: "",
    session_id: "",
    created_at: new Date().toISOString(),
    query: "",
    url: ""
  });
  const [doc, setDoc] = useState(null);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);

    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v ?? ""));
    if (doc) fd.append("doc", doc);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/runs/start`, {
        method: "POST",
        body: fd
      });
      const json = await res.json();
      setResult(json);
    } catch (err) {
      setResult({ error: String(err) });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Start a Build</h1>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <input className="border p-2 rounded" placeholder="Project ID" value={form.project_id} onChange={(e)=>update("project_id", e.target.value)} required/>
          <input className="border p-2 rounded" placeholder="User ID" value={form.user_id} onChange={(e)=>update("user_id", e.target.value)} required/>
          <input className="border p-2 rounded" placeholder="Session ID" value={form.session_id} onChange={(e)=>update("session_id", e.target.value)} required/>
          <input className="border p-2 rounded" placeholder="ISO timestamp" value={form.created_at} onChange={(e)=>update("created_at", e.target.value)} required/>
        </div>

        <textarea className="border p-2 rounded w-full" rows={4} placeholder="User query..." value={form.query} onChange={(e)=>update("query", e.target.value)} />
        <input className="border p-2 rounded w-full" placeholder="URL (optional)" value={form.url} onChange={(e)=>update("url", e.target.value)} />

        <input type="file" onChange={(e)=>setDoc(e.target.files?.[0] ?? null)} />

        <button disabled={submitting} className="px-4 py-2 rounded bg-black text-white">
          {submitting ? "Submitting..." : "Run"}
        </button>
      </form>

      {result && (
        <pre className="mt-6 bg-gray-50 p-4 rounded overflow-auto text-sm">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
