// src/components/IntentForm.jsx
import React from "react";
import { sendQuery } from "../api";

const MODELS = [
  "groq-default",
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-5",                 // alias → gpt-4o
  "claude-3-sonnet-20240229",
  "claude-3-5-sonnet-20240620",
  "sonnet-4",              // alias → claude-3-5-sonnet-20240620
];

const MODEL_DISPLAY_NAMES = {
  "groq-default": "Groq - Moonshot AI (Kimi K2) 🚀",
  "gpt-4o": "OpenAI GPT-4o",
  "gpt-4o-mini": "OpenAI GPT-4o Mini",
  "gpt-4-turbo": "OpenAI GPT-4 Turbo",
  "gpt-5": "OpenAI GPT‑5 (alias → GPT‑4o)",
  "claude-3-sonnet-20240229": "Claude 3 Sonnet (2024-02-29)",
  "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet (2024-06-20)",
  "sonnet-4": "Claude Sonnet 4 (alias → 3.5 Sonnet)",
};

function IntentForm() {
  // Generate a new session ID on every page refresh
  const [sessionId, setSessionId] = React.useState(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    console.log("🆕 Generated fresh session ID:", newSessionId);
    return newSessionId;
  });
  const [model, setModel] = React.useState("groq-default"); // Default to Groq
  const [text, setText] = React.useState("");
  const [file, setFile] = React.useState(null);
  const [sending, setSending] = React.useState(false);
  const [resp, setResp] = React.useState(null);
  const [error, setError] = React.useState("");

  const onFile = (e) => setFile(e.target.files?.[0] || null);
  const clearSession = () => { setSessionId(""); localStorage.removeItem("session_id"); };

  // ADD: Clear localStorage on component mount (page refresh)
  React.useEffect(() => {
    localStorage.removeItem("session_id");
    console.log("🔄 Page refreshed - session ID cleared");
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setSending(true); setError(""); setResp(null);
    try {
      const json = await sendQuery({ session_id: sessionId || undefined, text, llm_model: model, file });
      setResp(json);
      // DON'T persist session ID anymore - let each request be fresh
      if (json?.session_id) { 
        setSessionId(json.session_id); 
        // REMOVED: localStorage.setItem("session_id", json.session_id); 
      }
    } catch (err) {
      setError(err?.message || String(err));
    } finally { setSending(false); }
  }

  const generationResult = resp?.state?.context?.generation_result;
  const sandboxResult = resp?.state?.context?.sandbox_result;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%239C92AC%22%20fill-opacity%3D%220.05%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%221%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-30"></div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent mb-4">
            Growth 99
          </h1>
          <p className="text-slate-300 text-lg max-w-2xl mx-auto">
            A powerfull llm based UI page desginer.
          </p>
        </div>

        {/* Main form card */}
        <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-3xl shadow-2xl p-8 mb-8">
          <form onSubmit={onSubmit} className="space-y-6">
            {/* Session ID Row */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <label className="text-slate-200 font-medium min-w-[120px]">Session ID</label>
              <div className="flex-1 flex gap-3">
                <input
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  placeholder="(auto-created if empty)"
                  className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-xl text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 backdrop-blur-sm" />
                <button
                  type="button"
                  onClick={clearSession}
                  className="px-6 py-3 bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 hover:border-slate-500/50 text-slate-200 rounded-xl transition-all duration-200 backdrop-blur-sm hover:scale-105"
                >
                  Clear
                </button>
              </div>
            </div>

            {/* Model Selection */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <label className="text-slate-200 font-medium min-w-[120px]">AI Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 backdrop-blur-sm"
              >
                {MODELS.map(m => (
                  <option key={m} value={m}>
                    {MODEL_DISPLAY_NAMES[m] || m}
                  </option>
                ))}
              </select>
            </div>

            {/* Text Input */}
            <div className="flex flex-col sm:flex-row gap-4 items-start">
              <label className="text-slate-200 font-medium min-w-[120px] mt-3">Text</label>
              <textarea
                rows={4}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Describe your request or paste a URL. All analysis happens on the backend."
                required
                className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-xl text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 backdrop-blur-sm resize-none" />
            </div>

            {/* File Upload */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <label className="text-slate-200 font-medium min-w-[120px]">Upload Doc</label>
              <input
                type="file"
                onChange={onFile}
                className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-xl text-slate-200 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 transition-all duration-200 backdrop-blur-sm" />
            </div>

            {/* Submit Button */}
                        {/* Submit Button */}
                        <div className="flex justify-center pt-4 gap-3">
              <button
                type="submit"
                disabled={sending}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-slate-600 disabled:to-slate-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 disabled:cursor-not-allowed disabled:transform-none"
              >
                {sending ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Running...
                  </div>
                ) : (
                  "Run Pipeline"
                )}
              </button>

              {/* Regenerate Button */}
              {sandboxResult?.url && (
                <button
                  type="button"
                  disabled={sending}
                  onClick={async () => {
                    setSending(true); setError(""); 
                    try {
                      const json = await sendQuery({ session_id: sessionId || undefined, text, llm_model: model, regenerate: true });
                      setResp(json);
                      if (json?.session_id) { setSessionId(json.session_id); localStorage.setItem("session_id", json.session_id); }
                    } catch (err) {
                      setError(err?.message || String(err));
                    } finally { setSending(false); }
                  }}
                  className="px-8 py-4 bg-slate-700/60 hover:bg-slate-600/60 text-white font-semibold rounded-xl border border-slate-500/50 shadow hover:shadow-md transition-all duration-200"
                >
                  Regenerate
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Error Display */}
        {error && (
          <div className="backdrop-blur-xl bg-red-500/10 border border-red-500/20 rounded-2xl p-6 mb-8">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">!</span>
              </div>
              <div>
                <h3 className="text-red-300 font-semibold">Error</h3>
                <p className="text-red-200">{error}</p>
              </div>
            </div>
          </div>
        )}
        
        {/* Results Display */}
        {resp && (
          <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl shadow-2xl p-8">
            <h3 className="text-2xl font-bold text-white mb-6 text-center">Pipeline Results</h3>

            {/* NEW: Sandbox Result Section */}
            {sandboxResult && (
              <div className="bg-green-800/30 rounded-2xl p-6 border border-green-700/50 mb-6">
                <h4 className="text-lg font-semibold text-green-300 mb-3">Sandbox Preview</h4>
                {sandboxResult.url ? (
                  <div>
                    <p className="text-slate-300 mb-4">Your application is live!</p>
                    <a
                      href={sandboxResult.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-xl transition-all"
                    >
                      Open Preview
                    </a>
                  </div>
                ) : (
                  <p className="text-red-300">{sandboxResult.error || "Sandbox failed to start."}</p>
                )}
              </div>
            )}
            
            <div className="grid gap-6">
              {/* NEW: Generation Result Section */}
              {generationResult && (
                 <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50">
                    <h4 className="text-lg font-semibold text-pink-300 mb-3">Generated E2B Script</h4>
                    <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-xl overflow-x-auto border border-slate-700/30 max-h-96">
                      {generationResult.e2b_script || JSON.stringify(generationResult, null, 2)}
                    </pre>
                 </div>
              )}

              {/* Intent Section */}
              <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50">
                <h4 className="text-lg font-semibold text-purple-300 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                  Intent Analysis
                </h4>
                <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-xl overflow-x-auto border border-slate-700/30">
                  {JSON.stringify(resp.state?.context?.intent, null, 2)}
                </pre>
              </div>

              {/* Document Extraction */}
              <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50">
                <h4 className="text-lg font-semibold text-blue-300 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  Document Extraction
                </h4>
                <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-xl overflow-x-auto border border-slate-700/30">
                  {JSON.stringify(resp.state?.context?.extraction, null, 2)}
                </pre>
              </div>

              {/* URL Extraction */}
              <div className="bg-slate-800/30 rounded-2xl p-6 border border-slate-700/50">
                <h4 className="text-lg font-semibold text-green-300 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  URL Extraction
                </h4>
                <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-xl overflow-x-auto border border-slate-700/30">
                  {JSON.stringify(resp.state?.context?.url_extraction, null, 2)}
                </pre>
              </div>

              {/* Full State Details */}
              <details className="bg-slate-800/30 rounded-2xl border border-slate-700/50 overflow-hidden">
                <summary className="text-lg font-semibold text-slate-300 p-6 cursor-pointer hover:bg-slate-700/30 transition-colors duration-200">
                  Full State Details
                </summary>
                <div className="p-6 pt-0">
                  <pre className="text-sm text-slate-300 bg-slate-900/50 p-4 rounded-xl overflow-x-auto border border-slate-700/30">
                    {JSON.stringify(resp.state, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          </div>
        )}
      </div>

      {/* Custom CSS for animations */}
      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}

export default IntentForm;
