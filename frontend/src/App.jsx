import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import { Send, Bell, TrendingUp, DollarSign, Activity, Plus } from 'lucide-react';

function App() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState('default_user');
  const [activeTab, setActiveTab] = useState('chat');

  // Sample commands to show users what they can do
  const sampleCommands = [
    "Show my portfolio",
    "Add AAPL 10 shares at $150",
    "Alert me if TSLA drops below $200",
    "Compare AAPL vs GOOGL",
    "What if I buy 5 shares of NVDA?",
    "What's the price of MSFT?"
  ];

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = { type: 'user', content: message, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, user_id: userId })
      });

      const data = await response.json();
      
      const botMessage = {
        type: 'bot',
        content: data.response,
        intent: data.intent,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);

      // Update portfolio if it was a portfolio query
      if (data.intent?.action === 'show_portfolio' && data.response?.holdings) {
        setPortfolio(data.response);
      }

    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: { error: 'Failed to connect to chatbot service' },
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setMessage('');
    }
  };

  const loadPortfolio = async () => {
    try {
      const response = await fetch(`http://localhost:8000/portfolio/${userId}`);
      const data = await response.json();
      if (data && !data.error) {
        setPortfolio(data);
      }
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    }
  };

  useEffect(() => {
    loadPortfolio();
  }, []);

  const renderMessageContent = (content, messageType) => {
    if (typeof content === 'string') {
      return <div className="text-sm">{content}</div>;
    }

    if (content.error) {
      return <div className="text-red-600 text-sm">{content.error}</div>;
    }

    if (content.message) {
      return <div className="text-sm">{content.message}</div>;
    }

    if (content.stock_info) {
      const stock = content.stock_info;
      return (
        <div className="bg-white p-3 rounded border">
          <div className="font-semibold">{stock.name} ({stock.symbol})</div>
          <div className="text-lg font-bold text-green-600">${stock.current_price}</div>
          <div className="text-xs text-gray-600">
            {stock.sector} | Day Change: ${stock.day_change}
          </div>
        </div>
      );
    }

    if (content.comparison) {
      return (
        <div className="space-y-2">
          <div className="font-semibold text-sm">Stock Comparison:</div>
          {Object.entries(content.comparison).map(([symbol, data]) => (
            <div key={symbol} className="bg-white p-2 rounded border text-sm">
              <div className="font-medium">{data.name} ({symbol})</div>
              <div className="text-green-600">${data.current_price}</div>
              <div className="text-xs text-gray-600">{data.sector}</div>
            </div>
          ))}
        </div>
      );
    }

    if (content.simulation) {
      const sim = content.simulation;
      return (
        <div className="bg-blue-50 p-3 rounded border">
          <div className="font-semibold text-sm">Purchase Simulation</div>
          <div className="text-sm space-y-1">
            <div>{sim.quantity} shares of {sim.symbol} at ${sim.price_per_share}</div>
            <div>Total Cost: <span className="font-medium">${sim.total_cost}</span></div>
            <div>New Portfolio Value: <span className="font-medium">${sim.new_portfolio_value}</span></div>
          </div>
        </div>
      );
    }

    if (content.holdings) {
      return (
        <div className="space-y-2">
          <div className="font-semibold text-sm">Portfolio Summary</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>Total Value: <span className="font-medium text-green-600">${content.total_value}</span></div>
            <div>Total P&L: <span className={`font-medium ${content.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${content.total_profit_loss} ({content.total_profit_loss_pct}%)
            </span></div>
          </div>
          {content.holdings.slice(0, 3).map((holding, idx) => (
            <div key={idx} className="bg-white p-2 rounded border text-xs">
              <div className="font-medium">{holding.symbol}: {holding.quantity} shares</div>
              <div className="text-gray-600">
                ${holding.current_price} | P&L: <span className={holding.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}>
                  ${holding.profit_loss}
                </span>
              </div>
            </div>
          ))}
        </div>
      );
    }

    return <div className="text-sm">{JSON.stringify(content)}</div>;
  };

  const renderPortfolioCharts = () => {
    if (!portfolio || !portfolio.holdings) return null;

    const pieData = portfolio.holdings.map(holding => ({
      name: holding.symbol,
      value: holding.current_value,
      profit_loss: holding.profit_loss
    }));

    const COLORS = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'];

    return (
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Portfolio Allocation</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={60}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'Value']} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Profit/Loss by Holding</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={pieData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'P&L']} />
              <Bar dataKey="profit_loss" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-bold">Portfolio Chatbot</h1>
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1 rounded ${activeTab === 'chat' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`px-3 py-1 rounded ${activeTab === 'portfolio' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Portfolio
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-4">
        {activeTab === 'chat' && (
          <div className="grid md:grid-cols-3 gap-4">
            {/* Chat Interface */}
            <div className="md:col-span-2 bg-white rounded-lg border">
              <div className="p-4 border-b">
                <h2 className="font-semibold">Chat with your Portfolio Assistant</h2>
                <p className="text-sm text-gray-600">Ask about your portfolio, set alerts, compare stocks, or simulate trades</p>
              </div>

              {/* Messages */}
              <div className="h-96 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500">
                    <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>Start a conversation with your portfolio assistant!</p>
                  </div>
                )}
                
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs p-3 rounded-lg ${
                        msg.type === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {renderMessageContent(msg.content, msg.type)}
                      {msg.intent && (
                        <div className="text-xs opacity-75 mt-1">
                          Intent: {msg.intent.action}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-800 max-w-xs p-3 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce animation-delay-100"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce animation-delay-200"></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Input */}
              <div className="p-4 border-t">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me about your portfolio, stocks, or set alerts..."
                    className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isLoading}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={isLoading || !message.trim()}
                    className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Commands Sidebar */}
            <div className="bg-white rounded-lg border p-4">
              <h3 className="font-semibold mb-3">Quick Commands</h3>
              <div className="space-y-2">
                {sampleCommands.map((command, idx) => (
                  <button
                    key={idx}
                    onClick={() => setMessage(command)}
                    className="w-full text-left text-sm p-2 rounded bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    "{command}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'portfolio' && (
          <div className="space-y-6">
            {/* Portfolio Summary */}
            {portfolio && (
              <div className="bg-white rounded-lg border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold">Portfolio Overview</h2>
                  <button
                    onClick={loadPortfolio}
                    className="flex items-center space-x-2 bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                  >
                    <TrendingUp className="h-4 w-4" />
                    <span>Refresh</span>
                  </button>
                </div>

                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">Total Value</div>
                    <div className="text-2xl font-bold text-green-600">${portfolio.total_value}</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">Total Cost</div>
                    <div className="text-2xl font-bold">${portfolio.total_cost}</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">P&L</div>
                    <div className={`text-2xl font-bold ${portfolio.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${portfolio.total_profit_loss}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded">
                    <div className="text-sm text-gray-600">P&L %</div>
                    <div className={`text-2xl font-bold ${portfolio.total_profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {portfolio.total_profit_loss_pct}%
                    </div>
                  </div>
                </div>

                {renderPortfolioCharts()}
              </div>
            )}

            {/* Holdings Table */}
            {portfolio && portfolio.holdings && (
              <div className="bg-white rounded-lg border overflow-hidden">
                <div className="p-4 border-b">
                  <h3 className="font-semibold">Your Holdings</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Symbol</th>
                        <th className="px-4 py-2 text-left">Quantity</th>
                        <th className="px-4 py-2 text-left">Buy Price</th>
                        <th className="px-4 py-2 text-left">Current Price</th>
                        <th className="px-4 py-2 text-left">Current Value</th>
                        <th className="px-4 py-2 text-left">P&L</th>
                        <th className="px-4 py-2 text-left">P&L %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portfolio.holdings.map((holding, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-4 py-2 font-medium">{holding.symbol}</td>
                          <td className="px-4 py-2">{holding.quantity}</td>
                          <td className="px-4 py-2">${holding.buy_price}</td>
                          <td className="px-4 py-2">${holding.current_price}</td>
                          <td className="px-4 py-2">${holding.current_value}</td>
                          <td className={`px-4 py-2 ${holding.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${holding.profit_loss}
                          </td>
                          <td className={`px-4 py-2 ${holding.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {holding.profit_loss_pct}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {!portfolio && (
              <div className="bg-white rounded-lg border p-8 text-center">
                <DollarSign className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-semibold mb-2">No Portfolio Data</h3>
                <p className="text-gray-600 mb-4">Start by adding some holdings to your portfolio</p>
                <button
                  onClick={() => setActiveTab('chat')}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Go to Chat
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;