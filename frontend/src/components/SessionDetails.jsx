import React from "react";

function SessionDetails({ session, conversations, generatedLinks, onRestoreLink, onClose }) {
  return (
    <div className="bg-white border-r border-gray-200 w-96 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">{session.title}</h2>
          <p className="text-sm text-gray-500">
            Created {new Date(session.created_at).toLocaleDateString()}
          </p>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Generated Links Section */}
        {generatedLinks.length > 0 && (
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Generated Designs</h3>
            <div className="space-y-2">
              {generatedLinks.map((link, index) => (
                <div
                  key={link.id}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      Version {link.generation_number}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(link.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => onRestoreLink(link.id)}
                      className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                    >
                      Restore & Preview
                    </button>
                    {link.sandbox_url && (
                      <a
                        href={link.sandbox_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition-colors"
                      >
                        Open
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conversation History */}
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Conversation</h3>
          <div className="space-y-3">
            {conversations.map((conv) => (
              <div key={conv.id} className="space-y-2">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-900">{conv.user_query}</p>
                </div>
                {conv.ai_response && (
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-700">{conv.ai_response}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SessionDetails;
