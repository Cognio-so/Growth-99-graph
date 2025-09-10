// src/components/IntentForm.jsx
import React from "react";
import { sendQuery } from "../api";

const MODELS = [
  "k2",  // Single K2 option with automatic fallback
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-5",
  "claude-3-sonnet-20240229",
  "claude-3-5-sonnet-20240620",
  "sonnet-4",
  "glm-4.5",
  "gpt-oss-120b",  // New Groq model
  "groq-compound",  // New Groq Compound model
];

const MODEL_DISPLAY_NAMES = {
  "k2": "Kimi K2 (Moonshot) 🚀",
  "gpt-4o": "GPT-4o (OpenAI) 🤖",
  "gpt-4o-mini": "GPT-4o Mini (OpenAI) ⚡",
  "gpt-4-turbo": "GPT-4 Turbo (OpenAI) 🧠",
  "gpt-5": "GPT-5 (OpenAI) 🧠",
  "claude-3-sonnet-20240229": "Claude 3 Sonnet 🧠",
  "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet 🧠",
  "sonnet-4": "Claude Sonnet 4 🧠",
  "glm-4.5": "GLM-4.5 (ZhipuAI) 🤖",
  "gpt-oss-120b": "GPT-OSS-120B (Groq) 🚀",
  "groq-compound": "Groq Compound (Groq) ⚡"
};

function IntentForm() {
  const [sessionId, setSessionId] = React.useState(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return newSessionId;
  });
  const [model, setModel] = React.useState("k2"); // Default to K2
  const [text, setText] = React.useState("");
  const [file, setFile] = React.useState(null);
  const [logo, setLogo] = React.useState(null); // Add logo state
  const [sending, setSending] = React.useState(false);
  const [resp, setResp] = React.useState(null);
  const [error, setError] = React.useState("");
  const [showPreview, setShowPreview] = React.useState(false);

  // Update the file input to properly clear
  const onFile = (e) => setFile(e.target.files?.[0] || null);
  
  // Add logo file handler
  const onLogo = (e) => setLogo(e.target.files?.[0] || null);

  // Add a ref to the file input for programmatic clearing
  const fileInputRef = React.useRef(null);
  const logoInputRef = React.useRef(null); // Add logo input ref

  const clearSession = () => { 
    setSessionId(""); 
    localStorage.removeItem("session_id"); 
  };

  React.useEffect(() => {
    localStorage.removeItem("session_id");
  }, []);

  React.useEffect(() => {
    // Cleanup function to kill sandboxes on page refresh/close
    const handleBeforeUnload = async () => {
      try {
        // Send immediate cleanup request (don't wait for response)
        fetch('/api/cleanup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          keepalive: true  // Ensures request completes even if page closes
        });
      } catch (error) {
        console.log('Cleanup request failed:', error);
      }
    };

    // Add event listeners for page refresh/close
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('unload', handleBeforeUnload);

    // Cleanup on component unmount
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('unload', handleBeforeUnload);
      handleBeforeUnload(); // Also cleanup when component unmounts
    };
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setSending(true); 
    setError(""); 
    setResp(null);
    try {
      const json = await sendQuery({ session_id: sessionId || undefined, text, llm_model: model, file, logo });
      setResp(json);
      if (json?.session_id) { 
        setSessionId(json.session_id); 
      }
      
      // ENHANCED: Check if we should clear the form after edit operation
      if (json?.state?.context?.final_result?.clear_form) {
        console.log('Clearing form after edit operation with document');
        setText(""); // Clear text input
        setFile(null); // Clear file input
        setLogo(null); // Clear logo input
        // Clear the actual file input elements
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        if (logoInputRef.current) {
          logoInputRef.current.value = '';
        }
        // Note: We don't clear sessionId as it should persist for the session
      }
      
      // Automatically open preview in new tab when design is ready
      const sandboxUrl = json?.state?.context?.sandbox_result?.url;
      if (sandboxUrl) {
        console.log('Opening preview URL:', sandboxUrl);
        setTimeout(() => {
          window.open(sandboxUrl, '_blank');
        }, 1000); // Small delay to ensure the response is processed
      }
    } catch (err) {
      setError(err?.message || String(err));
    } finally { 
      setSending(false); 
    }
  }

  // Add regenerate function
  async function onRegenerate() {
    setSending(true); 
    setError(""); 
    setResp(null);
    try {
      const json = await sendQuery({ 
        session_id: sessionId || undefined, 
        text: text || "regenerate", 
        llm_model: model, 
        file, 
        logo,
        regenerate: true 
      });
      setResp(json);
      if (json?.session_id) { 
        setSessionId(json.session_id); 
      }
      
      // Automatically open preview in new tab when design is ready
      const sandboxUrl = json?.state?.context?.sandbox_result?.url;
      if (sandboxUrl) {
        console.log('Opening preview URL:', sandboxUrl);
        setTimeout(() => {
          window.open(sandboxUrl, '_blank');
        }, 1000); // Small delay to ensure the response is processed
      }
    } catch (err) {
      setError(err?.message || String(err));
    } finally { 
      setSending(false); 
    }
  }

  const generationResult = resp?.state?.context?.generation_result;
  const sandboxResult = resp?.state?.context?.sandbox_result;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900 to-orange-900 relative overflow-hidden">
      {/* Grainy texture overlay */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}></div>
      </div>

      {/* Header */}
      <div className="relative z-10 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-gradient-to-r from-purple-500 via-orange-500 to-pink-500 rounded-full mr-2"></div>
                  <span className="text-white text-xl font-bold">Growth 99</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* Session ID moved to navbar */}
              <div className="flex items-center space-x-2">
                <input
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  placeholder="Session ID"
                  className="px-3 py-2 bg-slate-800/50 border border-white/20 rounded-lg text-white placeholder-white/50 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all w-32"
                />
                <button
                  onClick={clearSession}
                  className="px-2 py-2 text-white/60 hover:text-white text-sm transition-colors"
                  title="Clear Session"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="px-6 py-2 bg-white text-slate-900 rounded-lg font-medium hover:bg-white/90 transition-colors"
              >
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-white mb-6">
            Build something{" "}
            <span className="inline-flex items-center">
              <span className="bg-gradient-to-r from-purple-500 via-orange-500 to-pink-500 bg-clip-text text-transparent">
                Great
              </span>
              <div className="w-6 h-6 bg-gradient-to-r from-purple-500 via-orange-500 to-pink-500 rounded-full ml-2"></div>
            </span>
          </h1>
          <p className="text-xl text-white/80 max-w-2xl mx-auto">
            Create design by chatting with AI.
          </p>
        </div>

        {/* Main Input Area */}
        <div className="mb-8">
          {/* Preview Link - Above the form */}
          {sandboxResult?.url && !sending && (
            <div className="text-center mb-6">
              <a
                href={sandboxResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-xl transition-colors"
              >
                <span>🎉 Your design is ready! Click to open preview</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          )}

          <div className="bg-slate-800/50 backdrop-blur-sm border border-white/20 rounded-2xl p-6">
            <form onSubmit={onSubmit} className="space-y-6">
              {/* Text Input with Upload Buttons */}
              <div>
                <div className="relative">
                  <textarea
                    rows={1}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Describe the UI/UX you want to create. Be specific about layout, components, and functionality."
                    required
                    className="w-full px-4 py-4 pr-20 bg-slate-700/50 border border-white/20 rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all resize-none text-lg"
                  />
                  {/* Upload Buttons Container */}
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex gap-2">
                    {/* Logo Upload Button */}
                    <label className="cursor-pointer" title="Upload Logo">
                      <input
                        ref={logoInputRef}
                        type="file"
                        onChange={onLogo}
                        className="hidden"
                        accept=".png,.jpg,.jpeg,.svg,.webp"
                      />
                      <div className="w-8 h-8 bg-orange-600 hover:bg-orange-700 rounded-lg flex items-center justify-center transition-colors">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                    </label>
                    
                    {/* Document Upload Button */}
                    <label className="cursor-pointer" title="Upload Document">
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={onFile}
                        className="hidden"
                        accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
                      />
                      <div className="w-8 h-8 bg-purple-600 hover:bg-purple-700 rounded-lg flex items-center justify-center transition-colors">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </div>
                    </label>
                  </div>
                </div>
                
                {/* Upload Status Display */}
                <div className="mt-2 space-y-2">
                  {/* Logo name display */}
                  {logo && (
                    <div className="flex items-center gap-2 text-sm text-orange-300">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Logo: {logo.name}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setLogo(null);
                          if (logoInputRef.current) logoInputRef.current.value = '';
                        }}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  )}
                  
                  {/* File name display */}
                  {file && (
                    <div className="flex items-center gap-2 text-sm text-white/70">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span>Document: {file.name}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setFile(null);
                          if (fileInputRef.current) fileInputRef.current.value = '';
                        }}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Model Selection - Centered below text area */}
              <div className="flex justify-center">
                <div className="w-64">
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-700/50 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-center"
                  >
                    {MODELS.map(m => (
                      <option key={m} value={m}>
                        {MODEL_DISPLAY_NAMES[m] || m}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Submit and Regenerate Buttons - Centered */}
              <div className="flex justify-center gap-4">
                <button
                  type="submit"
                  disabled={sending}
                  className="px-8 py-4 bg-gradient-to-r from-purple-500 via-orange-500 to-pink-500 text-white font-semibold rounded-xl hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg"
                >
                  {sending ? (
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                      <span>Creating...</span>
                    </div>
                  ) : (
                    "Create Design"
                  )}
                </button>
                
                {/* Regenerate Button - Only show if there's a previous result */}
                {sandboxResult?.url && !sending && (
                  <button
                    type="button"
                    onClick={onRegenerate}
                    disabled={sending}
                    className="px-6 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Regenerate
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Suggested Prompts */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {[
            { icon: "💻", text: "SaaS landing page" },
            { icon: "📚", text: "Hacker News top 100" },
            { icon: "<>", text: "Developer portfolio" },
            { icon: "🛍️", text: "E-commerce product page" }
          ].map((prompt, index) => (
            <button
              key={index}
              onClick={() => setText(prompt.text)}
              className="px-4 py-3 bg-slate-800/50 backdrop-blur-sm border border-white/20 rounded-xl text-white hover:bg-slate-700/50 transition-all text-center"
            >
              <div className="text-lg mb-1">{prompt.icon}</div>
              <div className="text-sm">{prompt.text}</div>
            </button>
          ))}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-8">
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <div>
                <h3 className="text-sm font-medium text-red-300">Error</h3>
                <p className="text-sm text-red-200">{error}</p>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Preview Panel - Fixed on the right */}
      {showPreview && (
        <div className="fixed right-0 top-0 h-full w-96 bg-slate-900/95 backdrop-blur-xl border-l border-white/20 z-50 overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-white">Live Preview</h2>
              <button
                onClick={() => setShowPreview(false)}
                className="text-white/60 hover:text-white transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Preview content would go here */}
            <div className="text-white/60 text-sm">
              Preview will appear here when available
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default IntentForm;
