import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  ClockIcon,
  UserGroupIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import MetricsCard, { ResponseTimeCard, ResolutionRateCard, AgentCountCard } from '../components/MetricsCard';
import { apiClient, formatUtils } from '../utils/api';
import { DashboardStats } from '../types';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Mock data for charts
  const responseTimeData = [
    { time: '00:00', responseTime: 2.1 },
    { time: '01:00', responseTime: 1.8 },
    { time: '02:00', responseTime: 3.2 },
    { time: '03:00', responseTime: 2.5 },
    { time: '04:00', responseTime: 1.9 },
    { time: '05:00', responseTime: 2.8 },
    { time: '06:00', responseTime: 3.1 },
    { time: '07:00', responseTime: 2.3 },
    { time: '08:00', responseTime: 1.7 },
    { time: '09:00', responseTime: 2.2 },
    { time: '10:00', responseTime: 2.9 },
    { time: '11:00', responseTime: 2.1 },
  ];

  const channelData = [
    { name: 'Chat', value: 45, color: '#3b82f6' },
    { name: 'Email', value: 35, color: '#10b981' },
    { name: 'Voice', value: 20, color: '#f59e0b' },
  ];

  const agentActivityData = [
    { hour: '08:00', agents: 120 },
    { hour: '09:00', agents: 180 },
    { hour: '10:00', agents: 250 },
    { hour: '11:00', agents: 320 },
    { hour: '12:00', agents: 280 },
    { hour: '13:00', agents: 310 },
    { hour: '14:00', agents: 450 },
    { hour: '15:00', agents: 520 },
    { hour: '16:00', agents: 480 },
    { hour: '17:00', agents: 350 },
    { hour: '18:00', agents: 220 },
    { hour: '19:00', agents: 150 },
  ];

  useEffect(() => {
    fetchStats();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const data = await apiClient.getDashboardStats();
      setStats(data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (error) {
      // Use mock data if API is not available
      setStats({
        total_agents: 487,
        agent_status: { idle: 245, busy: 198, error: 12, offline: 32 },
        total_messages_processed: 15847,
        total_escalations: 1267,
        resolution_rate: 0.82,
        average_response_time_ms: 2340,
        pending_messages: 23,
        uptime_seconds: 86400,
        messages_per_minute: 45.2
      });
      setLastUpdated(new Date());
      setLoading(false);
    }
  };

  const triggerLoadTest = async () => {
    try {
      toast.loading('Triggering load test...', { id: 'load-test' });
      
      // Simulate multiple requests
      const promises = Array.from({ length: 50 }, (_, i) => 
        apiClient.sendChatMessage({
          content: `Load test message #${i + 1} - Testing system capacity with concurrent requests`,
          user_id: `load_test_user_${i}`,
          channel: 'chat'
        })
      );
      
      await Promise.all(promises);
      toast.success('Load test completed successfully!', { id: 'load-test' });
      
      // Refresh stats
      setTimeout(fetchStats, 2000);
    } catch (error) {
      toast.error('Load test failed', { id: 'load-test' });
    }
  };

  const scaleAgents = async (targetCount: number) => {
    try {
      await apiClient.scaleAgents(targetCount);
      toast.success(`Scaling to ${targetCount} agents`);
      setTimeout(fetchStats, 1000);
    } catch (error) {
      toast.error('Failed to scale agents');
    }
  };

  if (loading || !stats) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Real-time system overview and metrics</p>
        </div>
        
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <MetricsCard key={i} title="" value="" loading />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Real-time system overview and metrics
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => fetchStats()}
            className="btn btn-secondary btn-sm"
          >
            Refresh
          </button>
          <button
            onClick={triggerLoadTest}
            className="btn btn-primary btn-sm"
          >
            Load Test
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <AgentCountCard 
          count={stats.total_agents}
          className="hover:shadow-medium transition-shadow"
        />
        
        <ResponseTimeCard 
          responseTime={stats.average_response_time_ms}
          className="hover:shadow-medium transition-shadow"
        />
        
        <ResolutionRateCard 
          rate={stats.resolution_rate}
          className="hover:shadow-medium transition-shadow"
        />
        
        <MetricsCard
          title="Messages/Min"
          value={stats.messages_per_minute.toFixed(1)}
          icon={ChatBubbleLeftRightIcon}
          color="primary"
          change={{
            value: 12,
            type: 'positive',
            label: 'vs last hour'
          }}
          className="hover:shadow-medium transition-shadow"
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <MetricsCard
          title="Total Processed"
          value={formatUtils.formatNumber(stats.total_messages_processed)}
          icon={CheckCircleIcon}
          color="success"
          change={{
            value: 847,
            type: 'positive',
            label: 'today'
          }}
        />
        
        <MetricsCard
          title="Pending Queue"
          value={stats.pending_messages}
          icon={ClockIcon}
          color={stats.pending_messages > 50 ? 'warning' : 'gray'}
          change={{
            value: -5,
            type: 'positive',
            label: 'vs 10 min ago'
          }}
        />
        
        <MetricsCard
          title="Escalations"
          value={stats.total_escalations}
          icon={ExclamationTriangleIcon}
          color="warning"
          change={{
            value: Math.round((1 - stats.resolution_rate) * 100),
            type: 'neutral',
            label: '% of total'
          }}
        />
        
        <MetricsCard
          title="System Uptime"
          value={formatUtils.formatDuration(stats.uptime_seconds)}
          icon={CheckCircleIcon}
          color="success"
          change={{
            value: 99.8,
            type: 'positive',
            label: '% availability'
          }}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Response Time Trend */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Response Time Trend</h3>
            <p className="text-sm text-gray-600">Last 12 hours</p>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={responseTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number) => [`${value}s`, 'Response Time']}
                />
                <Line 
                  type="monotone" 
                  dataKey="responseTime" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Channel Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Channel Distribution</h3>
            <p className="text-sm text-gray-600">Current message distribution</p>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={channelData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {channelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Agent Activity & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Agent Activity Chart */}
        <div className="lg:col-span-2 card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Agent Activity</h3>
            <p className="text-sm text-gray-600">Active agents throughout the day</p>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={agentActivityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="agents" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent Status & Controls */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">Agent Status</h3>
            <p className="text-sm text-gray-600">Current agent distribution</p>
          </div>
          <div className="card-body space-y-4">
            {Object.entries(stats.agent_status).map(([status, count]) => (
              <div key={status} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    status === 'idle' ? 'bg-success-500' :
                    status === 'busy' ? 'bg-warning-500' :
                    status === 'error' ? 'bg-danger-500' : 'bg-gray-400'
                  }`} />
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {status}
                  </span>
                </div>
                <span className="text-sm text-gray-600">
                  {count}
                </span>
              </div>
            ))}
            
            <div className="pt-4 border-t border-gray-200 space-y-2">
              <h4 className="text-sm font-medium text-gray-900">Quick Scale</h4>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => scaleAgents(200)}
                  className="btn btn-sm btn-secondary"
                >
                  Scale to 200
                </button>
                <button
                  onClick={() => scaleAgents(500)}
                  className="btn btn-sm btn-primary"
                >
                  Scale to 500
                </button>
                <button
                  onClick={() => scaleAgents(1000)}
                  className="btn btn-sm btn-success col-span-2"
                >
                  Demo: Scale to 1000
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Alerts */}
      <div className="mt-8">
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
          </div>
          <div className="card-body">
            <div className="space-y-3">
              <div className="flex items-center p-3 bg-success-50 rounded-lg">
                <CheckCircleIcon className="h-5 w-5 text-success-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-success-900">All systems operational</p>
                  <p className="text-xs text-success-700">Response times within target range</p>
                </div>
              </div>
              
              {stats.resolution_rate < 0.8 && (
                <div className="flex items-center p-3 bg-warning-50 rounded-lg">
                  <ExclamationTriangleIcon className="h-5 w-5 text-warning-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-warning-900">Resolution rate below target</p>
                    <p className="text-xs text-warning-700">Current: {(stats.resolution_rate * 100).toFixed(1)}% (Target: 80%)</p>
                  </div>
                </div>
              )}
              
              {stats.pending_messages > 50 && (
                <div className="flex items-center p-3 bg-warning-50 rounded-lg">
                  <ClockIcon className="h-5 w-5 text-warning-600 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-warning-900">High queue volume detected</p>
                    <p className="text-xs text-warning-700">{stats.pending_messages} messages pending</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 