// src/components/IntentForm.jsx
import React from "react";
import { sendQuery, downloadProjectFiles } from "../api";

// Add API_BASE configuration
const API_BASE =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  (typeof process !== "undefined" && process.env?.REACT_APP_API_URL) ||
  "https://growth-99-graph-production.up.railway.app"; // Update this line

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
    // Always create a new session ID on page refresh
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    console.log('🆕 Creating new session ID on page load:', newSessionId);
    return newSessionId;
  });
  const [model, setModel] = React.useState("k2"); // Default to K2
  const [text, setText] = React.useState("");
  const [file, setFile] = React.useState(null);
  const [logo, setLogo] = React.useState(null); // Add logo state
  const [image, setImage] = React.useState(null); // Add image state
  const [colorPalette, setColorPalette] = React.useState(""); // Add color palette state
  const [sending, setSending] = React.useState(false);
  const [resp, setResp] = React.useState(null);
  const [error, setError] = React.useState("");
  const [showPreview, setShowPreview] = React.useState(false);
  const [currentView, setCurrentView] = React.useState("initial"); // "initial" or "design"
  const [chatMessages, setChatMessages] = React.useState([]);
  const [chatInput, setChatInput] = React.useState("");

  // Add these new state variables:
  const [sessions, setSessions] = React.useState([]);
  const [selectedSession, setSelectedSession] = React.useState(null);
  const [sessionDetails, setSessionDetails] = React.useState(null);
  const [showSessionHistory, setShowSessionHistory] = React.useState(false);
  const [showSessionDetails, setShowSessionDetails] = React.useState(false);

  // Add a state to store the original current session ID:
  const [originalCurrentSessionId, setOriginalCurrentSessionId] = React.useState(null);

  // Add downloading state for the download button
  const [downloading, setDownloading] = React.useState(false);

  // Add state to track currently active conversation for download
  const [activeConversationId, setActiveConversationId] = React.useState(null);

  // Add state for design restoration loading
  const [restoringDesign, setRestoringDesign] = React.useState(false);

  // Add schema type state
  const [schemaType, setSchemaType] = React.useState("medspa");

  // Update the file input to properly clear
  const onFile = (e) => setFile(e.target.files?.[0] || null);
  
  // Add logo file handler
  const onLogo = (e) => setLogo(e.target.files?.[0] || null);

  // Add image file handler
  const onImage = (e) => setImage(e.target.files?.[0] || null);

  // Add a ref to the file input for programmatic clearing
  const fileInputRef = React.useRef(null);
  const logoInputRef = React.useRef(null); // Add logo input ref
  const imageInputRef = React.useRef(null); // Add image input ref
  const createNewSession = () => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    console.log('🆕 Creating new session ID:', newSessionId);
    setSessionId(newSessionId);
    return newSessionId;
  };
  // Add download function
  const handleDownloadCode = async () => {
    console.log('=== handleDownloadCode called ===');
    console.log('activeConversationId:', activeConversationId);
    console.log('sessionId:', sessionId);
    console.log('resp:', resp);
    
    if (!activeConversationId) {
      console.log('❌ No activeConversationId available');
      setError("No active design available for download");
      return;
    }

    setDownloading(true);
    try {
      console.log(' Starting download for conversationId:', activeConversationId);
      const blob = await downloadProjectFiles(activeConversationId);
      console.log('✅ Download completed, blob size:', blob.size);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:\-T]/g, '');
      a.download = `project_${activeConversationId.slice(0, 8)}_${timestamp}.zip`;
      
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      console.log('✅ Download initiated successfully');
    } catch (error) {
      console.error('❌ Download failed:', error);
      setError(`Download failed: ${error.message}`);
    } finally {
      setDownloading(false);
    }
  };

  const clearSession = () => { 
    setSessionId(""); 
    localStorage.removeItem("session_id"); 
  };

  // Add these new functions:
  const loadSessions = async () => {
    try {
      console.log('Loading sessions...');
      // FIX: Ensure no double slashes
      const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/sessions`;
      const response = await fetch(apiUrl);
      const data = await response.json();
      console.log('Sessions loaded:', data);
      setSessions(data.sessions || []);
      console.log('Sessions state updated:', data.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const loadSessionDetails = async (sessionId) => {
    try {
      // FIX: Ensure no double slashes
      const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/sessions/${sessionId}`;
      const response = await fetch(apiUrl);
      const data = await response.json();
      setSessionDetails(data);
      setShowSessionDetails(true);
    } catch (error) {
      console.error('Error loading session details:', error);
    }
  };

  // Add this function after the existing functions:
  const handleDeleteSession = async (sessionId, e) => {
    e.stopPropagation(); // Prevent opening the session when clicking delete
    
    if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      return;
    }
    
    try {
      // FIX: Ensure no double slashes
      const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/sessions/${sessionId}`;
      const response = await fetch(apiUrl, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete session');
      }
      
      // Remove from local state
      setSessions(prev => prev.filter(session => session.id !== sessionId));
      
      // If this was the current session, clear it
      if (sessionId === selectedSession?.id) {
        setSelectedSession(null);
        setCurrentView("initial");
      }
      
    } catch (error) {
      console.error('Error deleting session:', error);
      alert('Failed to delete session. Please try again.');
    }
  };

  // REMOVED: Redundant useEffect - session ID is now properly initialized above

  // Save session ID to localStorage when it changes
  React.useEffect(() => {
    if (sessionId) {
      localStorage.setItem('current_session_id', sessionId);
    }
  }, [sessionId]);

  // Add a function to switch between sessions
  const switchToSession = (newSessionId) => {
    setSessionId(newSessionId);
    setCurrentView("design");
    // Load the session details
    loadSessionDetails(newSessionId);
  };

  // Update the session history click handler
  const handleSelectSession = async (session) => {
    console.log('=== Opening session ===');
    console.log('Session:', session);
    console.log('Current sessionId before change:', sessionId);
    
    // Store the original current session ID if we haven't already
    if (!originalCurrentSessionId && sessionId) {
      setOriginalCurrentSessionId(sessionId);
      console.log('Stored original current session ID:', sessionId);
    }
    
    setSelectedSession(session);
    setSessionId(session.id);
    setCurrentView("design");
    
    // Load session details and conversation history
    try {
      console.log('Fetching session details for:', session.id);
      // FIX: Ensure no double slashes
      const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/sessions/${session.id}`;
      const response = await fetch(apiUrl);
      const data = await response.json();
      console.log('Session details received:', data);
      setSessionDetails(data);
      
      // Load conversation history and populate chat messages
      if (data.conversations && data.conversations.length > 0) {
        console.log('Found conversation history:', data.conversations);
        const chatMessages = [];
        
        data.conversations.forEach((conversation, index) => {
          console.log(`Processing conversation ${index}:`, conversation);
          console.log('conversation.id:', conversation.id);
          console.log('conversation.generated_code exists:', !!conversation.generated_code);
          console.log('conversation.generated_code length:', conversation.generated_code?.length || 0);
          
          // Add user message
          chatMessages.push({
            id: `user_${conversation.id}`,
            type: "user",
            content: conversation.user_query,
            timestamp: new Date(conversation.generation_timestamp)
          });
          
          // Add AI message with sandbox URL and conversation ID
          chatMessages.push({
            id: `ai_${conversation.id}`,
            type: "ai",
            content: conversation.ai_response || "I've generated your design based on your request.",
            timestamp: new Date(conversation.generation_timestamp),
            sandboxUrl: conversation.sandbox_url,
            conversationId: conversation.id, // Make sure this is set
            generationResult: conversation.generated_code ? JSON.parse(conversation.generated_code) : null
          });
        });
        
        console.log('Setting chat messages:', chatMessages);
        setChatMessages(chatMessages);
        
        // Set the latest sandbox URL as the current preview
        const latestConversation = data.conversations[data.conversations.length - 1];
        if (latestConversation.sandbox_url) {
          console.log('Setting preview URL:', latestConversation.sandbox_url);
          setResp({
            state: {
              context: {
                sandbox_result: {
                  url: latestConversation.sandbox_url
                },
                generation_result: latestConversation.generated_code ? JSON.parse(latestConversation.generated_code) : null
              }
            }
          });
          // Set the active conversation ID for download
          setActiveConversationId(latestConversation.id);
        }
      } else {
        console.log('No conversation history found');
        setChatMessages([]);
      }
      
      // Set the session title as the current text
      setText(session.title || "");
      
    } catch (error) {
      console.error('Error loading session details:', error);
      setChatMessages([]);
    }
  };

  const handleRestoreLink = async (linkId) => {
    if (!selectedSession) return;
    
    setSending(true);
    setError("");
    
    try {
      const formData = new FormData();
      formData.append("link_id", linkId);
      formData.append("text", "restore");
      
      // FIX: Ensure no double slashes
      const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/sessions/${selectedSession.id}/restore`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Failed to restore session');
      }
      
      const json = await response.json();
      setResp(json);
      
      // Automatically open preview
      const sandboxUrl = json?.state?.context?.sandbox_result?.url;
      if (sandboxUrl) {
        setTimeout(() => {
          window.open(sandboxUrl, '_blank');
        }, 1000);
      }
      
      // Close session details and refresh sessions
      setShowSessionDetails(false);
      loadSessions();
      
    } catch (err) {
      setError(err?.message || String(err));
    } finally {
      setSending(false);
    }
  };

  React.useEffect(() => {
    loadSessions();
  }, []);

  React.useEffect(() => {
    localStorage.removeItem("session_id");
  }, []);

  React.useEffect(() => {
    // Cleanup function to kill sandboxes on page refresh/close
    const handleBeforeUnload = async () => {
      try {
        // Send immediate cleanup request (don't wait for response)
        fetch(`${API_BASE}/api/cleanup`, {
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
    
    // Reset the original session ID when starting new design
    setOriginalCurrentSessionId(null);
    
    // Switch to design view immediately when user submits
    setCurrentView("design");
    setChatMessages([{
      id: Date.now(),
      type: "user",
      content: text,
      timestamp: new Date()
    }]);
    
    try {
      const json = await sendQuery({ 
        session_id: sessionId || undefined, 
        text, 
        llm_model: model, 
        file, 
        logo, 
        image, 
        color_palette: colorPalette,
        schema_type: schemaType  // Add schema type to request
      });
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
        setImage(null); // Clear image input
        setColorPalette(""); // Clear color palette input
        // Clear the actual file input elements
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        if (logoInputRef.current) {
          logoInputRef.current.value = '';
        }
        if (imageInputRef.current) {
          imageInputRef.current.value = '';
        }
        // Note: We don't clear sessionId as it should persist for the session
      } else {
        // Clear color palette after successful design generation
        setColorPalette("");
      }
      
      // Automatically open preview in new tab when design is ready
      const sandboxUrl = json?.state?.context?.sandbox_result?.url;
      if (sandboxUrl) {
        console.log('Opening preview URL:', sandboxUrl);
        setTimeout(() => {
          window.open(sandboxUrl, '_blank');
        }, 1000); // Small delay to ensure the response is processed
      }
      
      // ADD THIS LINE:
      loadSessions();
      
      // After getting the response, add the AI message with the sandbox URL:
      if (json?.state?.context?.sandbox_result?.url) {
        const aiMessage = {
          id: Date.now() + 1,
          type: "ai",
          content: "I've created your design! Check the preview below.",
          timestamp: new Date(),
          sandboxUrl: json.state.context.sandbox_result.url,
          conversationId: json.state.context.conversation_id, // Add conversationId
          generationResult: json.state.context.generation_result
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Set the active conversation ID for download
        if (json.state.context.conversation_id) {
          console.log('✅ Setting activeConversationId in onSubmit:', json.state.context.conversation_id);
          setActiveConversationId(json.state.context.conversation_id);
        } else {
          console.log('❌ No conversation_id in response:', json.state.context);
        }
      }
      
    } catch (err) {
      setError(err?.message || String(err));
    } finally { 
      setSending(false); 
    }
  }

  // Add regenerate function with schema type
  async function onRegenerate() {
    setSending(true); 
    setError(""); 
    setResp(null);
    try {
      const json = await sendQuery({ 
        session_id: sessionId || undefined, 
        text: "", // Let backend use stored original query instead of current form input
        llm_model: model, 
        file, 
        logo,
        image,
        color_palette: colorPalette,
        regenerate: true,
        schema_type: schemaType  // Add schema type to regenerate request
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
      
      // ADD THIS LINE:
      loadSessions();
      
    } catch (err) {
      setError(err?.message || String(err));
    } finally { 
      setSending(false); 
    }
  }

  // Chat function for design view with schema type
  async function onChatSubmit(e) {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      type: "user",
      content: chatInput,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput("");
    setSending(true);
    setError("");
    setResp(null); // Clear current preview to force iframe refresh
    
    try {
      const json = await sendQuery({ 
        session_id: sessionId || undefined, 
        text: chatInput, 
        llm_model: model, 
        file, 
        logo,
        image,
        color_palette: colorPalette,
        schema_type: schemaType  // Add schema type to chat requests
      });
      setResp(json);
      
      // Update the chat message structure to include generated links
      // In the onChatSubmit function, update the AI message creation:
      const aiMessage = {
        id: Date.now() + 1,
        type: "ai",
        content: "I've updated your design based on your request. Check the preview!",
        timestamp: new Date(),
        sandboxUrl: json?.state?.context?.sandbox_result?.url || null, // Add this
        conversationId: json?.state?.context?.conversation_id || null, // Add this
        generationResult: json?.state?.context?.generation_result || null // Add this
      };
      setChatMessages(prev => [...prev, aiMessage]);
      
      // Automatically open updated preview
      const sandboxUrl = json?.state?.context?.sandbox_result?.url;
      if (sandboxUrl) {
        setTimeout(() => {
          window.open(sandboxUrl, '_blank');
        }, 1000);
      }
      
      // Clear color palette after successful edit
      setColorPalette("");
      
      // ADD THIS LINE:
      loadSessions();
      
      // Set the active conversation ID for download
      if (json?.state?.context?.conversation_id) {
        console.log('✅ Setting activeConversationId in onChatSubmit:', json.state.context.conversation_id);
        setActiveConversationId(json.state.context.conversation_id);
      } else {
        console.log('❌ No conversation_id in response:', json?.state?.context);
      }
      
    } catch (err) {
      setError(err?.message || String(err));
    } finally {
      setSending(false);
    }
  }

  const generationResult = resp?.state?.context?.generation_result;
  const sandboxResult = resp?.state?.context?.sandbox_result;

  // Add this function after line 225 (after the handleSelectSession function ends):
  // Update the handleViewConversationDesign function with better debugging:
  const handleViewConversationDesign = async (conversationId, sandboxUrl) => {
    console.log('=== handleViewConversationDesign called ===');
    console.log('conversationId:', conversationId);
    console.log('sandboxUrl:', sandboxUrl);
    console.log('sessionDetails:', sessionDetails);
    console.log('sessionDetails.conversations:', sessionDetails?.conversations);
    console.log('current sessionId:', sessionId);
    
    if (!conversationId) {
      console.log('❌ No conversation ID available');
      return;
    }
    
    // Set restoring state to show loading immediately
    setRestoringDesign(true);
    
    // Clear the current preview URL so loading spinner shows instead of old sandbox
    setResp(null);
    
    try {
      // Check if this is from the current active session or a historical session
      const isCurrentActiveSession = selectedSession?.id === originalCurrentSessionId;
      console.log('isCurrentActiveSession (comparing with original):', isCurrentActiveSession);
      
      if (isCurrentActiveSession) {
        // This is from the current active session
        console.log('🔄 This is current active session');
        
        // Load session details if not already loaded
        if (!sessionDetails) {
          console.log(' Loading session details for current session');
          await loadSessionDetails(sessionId);
        }
        
        // Check if it's the latest conversation
        const latestConversation = sessionDetails?.conversations?.[sessionDetails.conversations.length - 1];
        const isLatestConversation = latestConversation?.id === conversationId;
        console.log('latestConversation:', latestConversation);
        console.log('isLatestConversation:', isLatestConversation);
        
        if (isLatestConversation) {
          // For the latest conversation in current session, use the current active sandbox
          console.log('✅ Opening latest design in current sandbox');
          window.open(sandboxUrl, '_blank');
        } else {
          // For older conversations in current session, apply the stored code
          console.log('🔄 Applying current session historical design to current sandbox');
          await applyStoredCodeToCurrentSandbox(conversationId);
        }
      } else {
        // This is from a historical session - always apply the stored code
        console.log('🔄 Applying historical session design to current sandbox');
        await applyStoredCodeToCurrentSandbox(conversationId);
      }
    } catch (error) {
      console.error('❌ Error in handleViewConversationDesign:', error);
    } finally {
      // Clear restoring state after a delay to allow the preview to load
      setTimeout(() => {
        setRestoringDesign(false);
      }, 5000); // Increased to 5 seconds to give more time
    }
  };

  // Update the applyStoredCodeToCurrentSandbox function to use the restore endpoint:
  const applyStoredCodeToCurrentSandbox = async (conversationId) => {
    console.log('🔄 applyStoredCodeToCurrentSandbox called with conversationId:', conversationId);
    
    // First try to get conversation from sessionDetails
    let conversation = sessionDetails?.conversations?.find(conv => conv.id === conversationId);
    console.log('Found conversation in sessionDetails:', conversation);
    
    // If not found in sessionDetails, try to get it from chat messages
    if (!conversation) {
      console.log('🔄 Conversation not found in sessionDetails, trying to load session details');
      try {
        await loadSessionDetails(sessionId);
        conversation = sessionDetails?.conversations?.find(conv => conv.id === conversationId);
        console.log('Found conversation after loading session details:', conversation);
      } catch (error) {
        console.error('❌ Error loading session details:', error);
      }
    }
    
    if (!conversation) {
      console.log('❌ No conversation found with ID:', conversationId);
      return;
    }
    
    if (!conversation.generated_code) {
      console.log('❌ No stored code found for this conversation');
      console.log('conversation.generated_code:', conversation.generated_code);
      // Fallback to current preview
      const currentUrl = resp?.state?.context?.sandbox_result?.url;
      if (currentUrl) {
        window.open(currentUrl, '_blank');
      }
      return;
    }
    
    console.log('✅ Found stored code, length:', conversation.generated_code.length);
    
    try {
      // Use the current session ID
      const correctSessionId = sessionId;
      console.log('🚀 Restoring design to current sandbox...');
      console.log('Using session ID:', correctSessionId);
      console.log('Conversation ID:', conversationId);
      
      // Call the restore endpoint
      const apiUrl = `${API_BASE.replace(/\/$/, '')}/api/sessions/${correctSessionId}/conversations/${conversationId}/restore`;
      console.log('API URL:', apiUrl);
      
      const restoreResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Restore response status:', restoreResponse.status);
      
      if (restoreResponse.ok) {
        const restoreData = await restoreResponse.json();
        console.log('✅ Restored design to current sandbox');
        console.log('Restore data:', restoreData);
        
        // Update the current preview to show the restored design
        setResp({
          state: {
            context: {
              sandbox_result: {
                url: restoreData.sandbox_url
              },
              generation_result: conversation.generated_code ? JSON.parse(conversation.generated_code) : null
            }
          }
        });
        
        // Open the restored sandbox
        if (restoreData.sandbox_url) {
          console.log('✅ Opening restored sandbox:', restoreData.sandbox_url);
          window.open(restoreData.sandbox_url, '_blank');
        }
      } else {
        console.error('❌ Failed to restore design, status:', restoreResponse.status);
        const errorText = await restoreResponse.text();
        console.error('Error response:', errorText);
        // Fallback to current preview
        const currentUrl = resp?.state?.context?.sandbox_result?.url;
        if (currentUrl) {
          window.open(currentUrl, '_blank');
        }
      }
    } catch (error) {
      console.error('❌ Error restoring design:', error);
      // Fallback to current preview
      const currentUrl = resp?.state?.context?.sandbox_result?.url;
      if (currentUrl) {
        window.open(currentUrl, '_blank');
      }
    }
  };

  // Add this new function for current session conversations
  const applyCurrentSessionDesign = async (conversationId) => {
    console.log('🔄 Applying current session design:', conversationId);
    
    // Get the stored conversation data
    const conversation = sessionDetails?.conversations?.find(conv => conv.id === conversationId);
    console.log('Found conversation:', conversation);
    
    if (!conversation) {
      console.log('❌ No conversation found with ID:', conversationId);
      return;
    }
    
    if (!conversation.generated_code) {
      console.log('❌ No stored code found for this conversation');
      return;
    }
    
    try {
      // Set restoring state
      setRestoringDesign(true);
      setResp(null);
      
      // Send the stored code as an edit request to apply it to current sandbox
      const json = await sendQuery({ 
        session_id: sessionId || undefined, 
        text: `restore_design:${conversationId}`, // Special command to restore design
        llm_model: model, 
        file: null,
        logo: null,
        image: null,
        color_palette: colorPalette
      });
      
      setResp(json);
      
      // Update the preview
      const sandboxUrl = json?.state?.context?.sandbox_result?.url;
      if (sandboxUrl) {
        console.log('✅ Applied current session design to sandbox');
      }
      
    } catch (error) {
      console.error('❌ Error applying current session design:', error);
    } finally {
      setTimeout(() => {
        setRestoringDesign(false);
      }, 3000);
    }
  };

  // Add a function to manage current session states:
  const handleViewCurrentSessionDesign = (conversationId, sandboxUrl) => {
    console.log('Viewing current session design:', conversationId);
    
    // Add state parameter to the URL to identify which design state to show
    const stateParam = `?state=${conversationId.slice(-4)}`;
    const urlWithState = sandboxUrl + stateParam;
    
    console.log('Opening with state parameter:', urlWithState);
    window.open(urlWithState, '_blank');
  };

  // Update the chat message rendering to use different handlers:
  const renderChatMessage = (message) => {
    const isUser = message.type === "user";
    const isAi = message.type === "ai";
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-200 text-gray-800'
        }`}>
          <p className="text-sm">{message.content}</p>
          {isAi && message.sandboxUrl && (
            <div className="mt-2">
              <button
                onClick={() => {
                  // Check if this is current session or historical
                  const latestConversation = sessionDetails?.conversations?.[sessionDetails.conversations.length - 1];
                  const isLatestConversation = latestConversation?.id === message.conversationId;
                  
                  if (isLatestConversation) {
                    handleViewCurrentSessionDesign(message.conversationId, message.sandboxUrl);
                  } else {
                    handleViewConversationDesign(message.conversationId, message.sandboxUrl);
                  }
                }}
                className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-xs"
              >
                View Design {message.conversationId ? `#${message.conversationId.slice(-4)}` : ''}
              </button>
            </div>
          )}
          <p className="text-xs opacity-70 mt-1">
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  };

  // Initial view - the original form
  if (currentView === "initial") {
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
                      
                      {/* Image Upload Button */}
                      <label className="cursor-pointer" title="Upload Image">
                        <input
                          ref={imageInputRef}
                          type="file"
                          onChange={onImage}
                          className="hidden"
                          accept=".png,.jpg,.jpeg,.svg,.webp,.gif"
                        />
                        <div className="w-8 h-8 bg-green-600 hover:bg-green-700 rounded-lg flex items-center justify-center transition-colors">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
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
                    
                    {/* Image name display */}
                    {image && (
                      <div className="flex items-center gap-2 text-sm text-green-300">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>Image: {image.name}</span>
                        <button
                          type="button"
                          onClick={() => {
                            setImage(null);
                            if (imageInputRef.current) imageInputRef.current.value = '';
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

                {/* Color Palette Input */}
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Color Palette
                  </label>
                  <textarea
                    rows={2}
                    value={colorPalette}
                    onChange={(e) => setColorPalette(e.target.value)}
                    placeholder="blue, #FF5733, yellow..."
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm resize-none"
                  />
                </div>

                {/* Schema Type Selection */}
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Design Schema
                  </label>
                  <select
                    value={schemaType}
                    onChange={(e) => setSchemaType(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  >
                    <option value="medspa">Medspa & Beauty 💄</option>
                    <option value="dental">Dental & Medical 🦷</option>
                  </select>
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

                {/* Submit Button - Centered */}
                <div className="flex justify-center">
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

          {/* Gallery Section - Show if sessions exist */}
          {sessions.length > 0 && (
            <div className="mb-12">
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-white mb-4">Your Previous Designs</h2>
                <p className="text-white/70">Click on any design to continue working on it</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className="bg-slate-800/50 backdrop-blur-sm border border-white/20 rounded-xl p-6 hover:bg-slate-700/50 transition-all cursor-pointer relative group"
                    onClick={() => handleSelectSession(session)}
                  >
                    {/* Add delete button */}
                    <button
                      onClick={(e) => handleDeleteSession(session.id, e)}
                      className="absolute top-2 right-2 w-6 h-6 bg-red-500/80 hover:bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Delete session"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    
                    <div className="aspect-video bg-gradient-to-br from-purple-500/20 to-orange-500/20 rounded-lg flex items-center justify-center mb-4">
                      <div className="text-center">
                        <div className="w-12 h-12 bg-white/10 rounded-lg flex items-center justify-center mx-auto mb-2">
                          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <p className="text-sm text-white/70">Design Preview</p>
                      </div>
                    </div>
                    
                    <h3 className="text-white font-medium mb-2 truncate">
                      {session.title || "Untitled Design"}
                    </h3>
                    <p className="text-white/60 text-sm mb-2">
                      {session.message_count} messages
                    </p>
                    <p className="text-white/40 text-xs">
                      {new Date(session.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

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
      </div>
    );
  }

  // Design view - Lovable-like interface
  return (
    <div className="h-screen bg-gray-100 flex flex-col">
      {/* Top Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <div className="w-6 h-6 bg-gradient-to-r from-purple-500 via-orange-500 to-pink-500 rounded-full mr-2"></div>
            <span className="text-gray-900 text-lg font-semibold">Growth 99</span>
          </div>
          <div className="text-sm text-gray-500">Previewing last saved version</div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => {
              createNewSession();
              setCurrentView("initial");
            }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
          >
            New Design
          </button>
        </div>
      </div>

      {/* Main Content - Two Panel Layout */}
      <div className="flex-1 flex">
        {/* Left Sidebar */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* Project Info */}
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-white text-lg font-semibold mb-2">Your Design</h2>
            <div className="text-gray-300 text-sm mb-4">
              {text}
            </div>
            
            {/* Generated Link Button */}
            {sandboxResult?.url && (
              <a
                href={sandboxResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Open Generated Link
              </a>
            )}
          </div>

          {/* Chat Section */}
          <div className="flex-1 flex flex-col">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-white font-medium">Chat with AI</h3>
            </div>
            
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex flex-col ${message.type === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-200'
                    }`}
                  >
                    {message.content}
                  </div>
                  
                  {/* Add generated link button for AI messages with sandbox URL */}
                  {message.type === 'ai' && message.sandboxUrl && (
                    <div className="mt-2">
                      <button
                        onClick={() => handleViewConversationDesign(message.conversationId, message.sandboxUrl)}
                        className="inline-flex items-center gap-2 px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg transition-colors"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        View Design {message.conversationId ? `#${message.conversationId.slice(-4)}` : ''}
                      </button>
                    </div>
                  )}
                </div>
              ))}
              
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 text-gray-200 px-3 py-2 rounded-lg text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                      <span>AI is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Chat Input */}
            <div className="p-4 border-t border-gray-700">
              <form onSubmit={onChatSubmit} className="space-y-3">
                {/* Upload Options Row */}
                <div className="flex gap-2">
                  {/* Logo Upload */}
                  <label className="cursor-pointer flex items-center gap-2 px-3 py-2 bg-orange-600/20 hover:bg-orange-600/30 border border-orange-500/30 rounded-lg transition-colors text-orange-300 text-sm" title="Upload Logo">
                    <input
                      ref={logoInputRef}
                      type="file"
                      onChange={onLogo}
                      className="hidden"
                      accept=".png,.jpg,.jpeg,.svg,.webp"
                    />
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Logo
                  </label>
                  
                  {/* Document Upload */}
                  <label className="cursor-pointer flex items-center gap-2 px-3 py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg transition-colors text-purple-300 text-sm" title="Upload Document">
                    <input
                      ref={fileInputRef}
                      type="file"
                      onChange={onFile}
                      className="hidden"
                      accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
                    />
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Doc
                  </label>
                  
                  {/* Image Upload */}
                  <label className="cursor-pointer flex items-center gap-2 px-3 py-2 bg-green-600/20 hover:bg-green-600/30 border border-green-500/30 rounded-lg transition-colors text-green-300 text-sm" title="Upload Image">
                    <input
                      ref={imageInputRef}
                      type="file"
                      onChange={onImage}
                      className="hidden"
                      accept=".png,.jpg,.jpeg,.svg,.webp,.gif"
                    />
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Image
                  </label>
                  
                  
                  
                  {/* Model Selection */}
                  <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {MODELS.map(m => (
                      <option key={m} value={m}>
                        {MODEL_DISPLAY_NAMES[m] || m}
                      </option>
                    ))}
                  </select>

                  {/* Schema Type Selection */}
                  <select
                    value={schemaType}
                    onChange={(e) => setSchemaType(e.target.value)}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="medspa">Medspa 💄</option>
                    <option value="dental">Dental 🦷</option>
                  </select>
                </div>
                
                {/* Upload Status Display */}
                {(logo || file || image) && (
                  <div className="space-y-1">
                    {logo && (
                      <div className="flex items-center gap-2 text-xs text-orange-300">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    )}
                    
                    {file && (
                      <div className="flex items-center gap-2 text-xs text-purple-300">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Doc: {file.name}</span>
                        <button
                          type="button"
                          onClick={() => {
                            setFile(null);
                            if (fileInputRef.current) fileInputRef.current.value = '';
                          }}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    )}

                    {image && (
                      <div className="flex items-center gap-2 text-xs text-green-300">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>Image: {image.name}</span>
                        <button
                          type="button"
                          onClick={() => {
                            setImage(null);
                            if (imageInputRef.current) imageInputRef.current.value = '';
                          }}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Text Input and Send Button */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask for changes..."
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                  <button
                    type="submit"
                    disabled={sending || !chatInput.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors text-sm"
                  >
                    Send
                  </button>
                </div>
                
                {/* Regenerate Button */}
                <button
                  type="button"
                  onClick={onRegenerate}
                  disabled={sending}
                  className="w-full px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-gray-500 disabled:to-gray-600 text-white rounded-lg transition-all text-sm flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Regenerate Design
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Right Preview Area */}
        <div className="flex-1 flex flex-col">
          {/* Preview Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h3 className="text-gray-900 font-medium">Live Preview</h3>
              {sandboxResult?.url ? (
                <span className="text-sm text-green-600 bg-green-50 px-2 py-1 rounded">
                  ✓ Design Ready
                </span>
              ) : sending ? (
                <span className="text-sm text-blue-600 bg-blue-50 px-2 py-1 rounded flex items-center gap-1">
                  <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  Creating...
                </span>
              ) : (
                <span className="text-sm text-gray-500 bg-gray-50 px-2 py-1 rounded">
                  Waiting for design...
                </span>
              )}
            </div>
            
            {sandboxResult?.url && (
              <div className="flex items-center space-x-2">
                {/* Schema Type Selection in Preview Header */}
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-600 font-medium">Schema:</label>
                  <select
                    value={schemaType}
                    onChange={(e) => setSchemaType(e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="medspa">Medspa 💄</option>
                    <option value="dental">Dental 🦷</option>
                  </select>
                </div>
                
                {/* Add Color Palette Input */}
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-600 font-medium">Colors:</label>
                  <input
                    type="text"
                    value={colorPalette}
                    onChange={(e) => setColorPalette(e.target.value)}
                    placeholder="blue, #FF5733, yellow..."
                    className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-48"
                  />
                </div>
                
                <button
                  onClick={handleDownloadCode}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2"
                  disabled={downloading}
                >
                  {downloading ? (
                    <div className="w-4 h-4 border border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  )}
                  {downloading ? "Downloading..." : "Download Code"}
                </button>
                <a
                  href={sandboxResult.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  Open in Full Page
                </a>
              </div>
            )}
          </div>
          
          {/* Preview Content */}
          <div className="flex-1 bg-gray-50 flex items-center justify-center">
            {sandboxResult?.url ? (
              <div className="w-full h-full">
                <iframe
                  src={sandboxResult.url}
                  className="w-full h-full border-0"
                  title="Design Preview"
                  key={sandboxResult.url}
                />
              </div>
            ) : (
              <div className="text-center text-gray-500">
                <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                  {sending ? (
                    <div className="w-8 h-8 border-4 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
                  ) : restoringDesign ? (
                    <div className="w-8 h-8 border-4 border-gray-300 border-t-green-600 rounded-full animate-spin"></div>
                  ) : (
                    <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  )}
                </div>
                <p className="text-lg font-medium mb-2">
                  {sending ? "Creating your design..." : restoringDesign ? "Restoring your design..." : "Preview will appear here"}
                </p>
                <p className="text-sm">
                  {sending ? "Please wait while we generate your design" : restoringDesign ? "Your design is being restored from history" : "Your generated design will be displayed in this area"}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-t border-red-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">!</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default IntentForm;
