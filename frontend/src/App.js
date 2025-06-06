import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('⚙️ Testing');
  const [isLoading, setIsLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load dashboard data on mount
    if (activeTab === 'dashboard') {
      loadDashboardData();
    }
  }, [activeTab]);

  const testAPI = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      
      if (response.ok) {
        setApiStatus('✅ Connected');
        console.log('API Response:', data);
      } else {
        setApiStatus('❌ Error');
      }
    } catch (error) {
      setApiStatus('❌ Failed');
      console.error('API Error:', error);
    }
    setIsLoading(false);
  };

  const loadDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/dashboard/stats');
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Dashboard data error:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: inputMessage,
          conversation_id: conversationId
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        if (!conversationId) {
          setConversationId(data.conversation_id);
        }

        const aiMessage = {
          role: 'assistant',
          content: data.response,
          confidence: data.confidence,
          agent_id: data.agent_id,
          response_time: data.response_time,
          timestamp: Date.now()
        };

        setMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
    
    setIsTyping(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🚀 Agentic Communications V1
              </h1>
              <span className="ml-3 text-sm text-gray-500">AI-Powered Multi-Channel Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                apiStatus.includes('✅') ? 'bg-green-100 text-green-800' :
                apiStatus.includes('❌') ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {apiStatus}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['dashboard', 'console', 'email'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab === 'console' ? '💬 Chat Console' : 
                 tab === 'dashboard' ? '📊 Dashboard' : 
                 '📧 Email Hub'}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {activeTab === 'dashboard' && (
          <div className="px-4 py-6 sm:px-0">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Metrics Cards */}
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="text-2xl">⚡</div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Avg Response Time
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {dashboardData ? `${dashboardData.avg_response_time}s` : '...'}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="text-2xl">🎯</div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Auto Resolution Rate
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {dashboardData ? `${(dashboardData.auto_resolution_rate * 100).toFixed(1)}%` : '...'}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="text-2xl">🤖</div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Active Agents
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {dashboardData ? dashboardData.active_agents : '...'}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="text-2xl">💬</div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total Conversations
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {dashboardData ? dashboardData.total_conversations : '...'}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Test API Section */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">System Status</h3>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">
                    Backend API Status: <span className="font-medium">{apiStatus}</span>
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Uptime: {dashboardData ? `${dashboardData.uptime_hours}h` : '...'} | Queue: {dashboardData ? dashboardData.queue_length : '...'} pending
                  </p>
                </div>
                <button 
                  onClick={testAPI}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  {isLoading ? '🔄 Testing...' : '🔧 Test Connection'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'console' && (
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-white shadow rounded-lg h-96 flex flex-col">
              {/* Chat Header */}
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-medium text-gray-900">AI Chat Console</h3>
                <p className="text-sm text-gray-600">Test the AI assistant capabilities</p>
              </div>
              
              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    <div className="text-4xl mb-2">💬</div>
                    <p>Start a conversation with our AI assistant</p>
                    <p className="text-sm mt-1">Try: "Hello", "What are your features?", or "What's your pricing?"</p>
                  </div>
                )}
                
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      {message.confidence && (
                        <p className="text-xs mt-1 opacity-75">
                          Confidence: {(message.confidence * 100).toFixed(1)}% | 
                          Agent: {message.agent_id} |
                          {message.response_time ? ` ${(message.response_time * 1000).toFixed(0)}ms` : ''}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-gray-100">
                      <p className="text-sm text-gray-600">AI is typing...</p>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
              
              {/* Input */}
              <div className="px-6 py-4 border-t">
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message..."
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isTyping}
                  />
                  <button
                    onClick={sendMessage}
                    disabled={isTyping || !inputMessage.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'email' && (
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Email Processing Hub</h3>
              <div className="text-center py-8 text-gray-500">
                <div className="text-4xl mb-2">📧</div>
                <p>Email processing features coming soon...</p>
                <p className="text-sm mt-1">Auto-response, classification, and escalation</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App; 