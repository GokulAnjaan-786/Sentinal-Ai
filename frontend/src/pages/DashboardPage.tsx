/**
 * Dashboard Page
 * ================
 * Main SOC dashboard with key metrics, charts, and real-time data.
 * Provides an overview of the organization's security posture.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users, Shield, AlertTriangle, Activity, TrendingUp,
  Eye, Clock, Server,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar,
  Legend,
} from 'recharts';
import { dashboardApi, riskApi } from '../services/api';
import type { DashboardSummary, ThreatTimeline } from '../types';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#10b981',
};

const RISK_COLORS = ['#10b981', '#f59e0b', '#f97316', '#ef4444'];

/**
 * Stat Card Component
 * Displays a single metric with icon, value, and label.
 */
function StatCard({ icon: Icon, label, value, color, delay }: {
  icon: any; label: string; value: string | number; color: string; delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="cyber-card-hover"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="stat-label">{label}</p>
          <p className="stat-number mt-1">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </motion.div>
  );
}

/**
 * Custom Tooltip for Recharts
 */
function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-cyber-card border border-cyber-border rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [timeline, setTimeline] = useState<ThreatTimeline | null>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [topRisk, setTopRisk] = useState<any[]>([]);
  const [scorecard, setScorecard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [summaryData, timelineData, activityData, riskData, scorecardData] = await Promise.allSettled([
        dashboardApi.getSummary(),
        dashboardApi.getTimeline(7),
        dashboardApi.getRecentActivity(10),
        riskApi.getTopRisk(5),
        dashboardApi.getScorecard(),
      ]);

      if (summaryData.status === 'fulfilled') setSummary(summaryData.value);
      if (timelineData.status === 'fulfilled') setTimeline(timelineData.value);
      if (activityData.status === 'fulfilled') setRecentActivity(activityData.value);
      if (riskData.status === 'fulfilled') setTopRisk(riskData.value.top_risk_users || []);
      if (scorecardData.status === 'fulfilled') setScorecard(scorecardData.value);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-glow mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  // Prepare timeline chart data
  const timelineChartData = timeline ? timeline.timestamps.map((ts, i) => ({
    date: new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    critical: timeline.critical_counts[i] || 0,
    high: timeline.high_counts[i] || 0,
    medium: timeline.medium_counts[i] || 0,
    low: timeline.low_counts[i] || 0,
    total: timeline.total_counts[i] || 0,
  })) : [];

  // Risk distribution for pie chart
  const riskDistribution = summary ? [
    { name: 'Low', value: summary.total_users - summary.users_at_risk - summary.users_critical },
    { name: 'Medium', value: summary.users_at_risk },
    { name: 'High', value: Math.floor(summary.users_at_risk * 0.5) },
    { name: 'Critical', value: summary.users_critical },
  ] : [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Security Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">Real-time threat monitoring and analytics</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Total Users" value={summary?.total_users || 0} color="bg-blue-500/20 text-blue-400" delay={0} />
        <StatCard icon={AlertTriangle} label="Active Alerts" value={summary?.total_alerts_today || 0} color="bg-red-500/20 text-red-400" delay={0.1} />
        <StatCard icon={Shield} label="Avg Risk Score" value={`${summary?.average_risk_score || 0}`} color="bg-yellow-500/20 text-yellow-400" delay={0.2} />
        <StatCard icon={Activity} label="Activities Today" value={summary?.total_activities_today || 0} color="bg-green-500/20 text-green-400" delay={0.3} />
      </div>

      {/* Alert Severity Cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Critical', value: summary?.critical_alerts || 0, color: 'bg-red-500', textColor: 'text-red-400' },
          { label: 'High', value: summary?.high_alerts || 0, color: 'bg-orange-500', textColor: 'text-orange-400' },
          { label: 'Medium', value: summary?.medium_alerts || 0, color: 'bg-yellow-500', textColor: 'text-yellow-400' },
          { label: 'Low', value: summary?.low_alerts || 0, color: 'bg-green-500', textColor: 'text-green-400' },
        ].map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 + i * 0.05 }}
            className="cyber-card text-center py-4"
          >
            <div className={`w-2 h-2 ${item.color} rounded-full mx-auto mb-2 animate-pulse`}></div>
            <p className={`text-2xl font-bold ${item.textColor}`}>{item.value}</p>
            <p className="text-xs text-gray-400 mt-1">{item.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Threat Timeline Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="lg:col-span-2 cyber-card"
        >
          <h3 className="text-sm font-semibold text-white mb-4">Threat Timeline (7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timelineChartData}>
              <defs>
                <linearGradient id="colorCritical" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorHigh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorMedium" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="critical" stroke="#ef4444" fill="url(#colorCritical)" name="Critical" />
              <Area type="monotone" dataKey="high" stroke="#f97316" fill="url(#colorHigh)" name="High" />
              <Area type="monotone" dataKey="medium" stroke="#f59e0b" fill="url(#colorMedium)" name="Medium" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Risk Distribution Pie Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="cyber-card"
        >
          <h3 className="text-sm font-semibold text-white mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={riskDistribution}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
              >
                {riskDistribution.map((_, index) => (
                  <Cell key={index} fill={RISK_COLORS[index % RISK_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {riskDistribution.map((entry, i) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: RISK_COLORS[i] }}></div>
                <span className="text-[11px] text-gray-400">{entry.name}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Risk Users */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="cyber-card"
        >
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-red-400" />
            Top Risk Users
          </h3>
          <div className="space-y-3">
            {topRisk.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No risk data available</p>
            ) : (
              topRisk.map((user: any, i: number) => (
                <div key={user.user_id} className="flex items-center gap-3 p-3 bg-cyber-dark rounded-lg border border-cyber-border">
                  <div className="w-8 h-8 bg-cyber-glow/20 rounded-full flex items-center justify-center border border-cyber-glow/30">
                    <span className="text-xs font-bold text-cyber-glow">{i + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
                    <p className="text-[11px] text-gray-500">{user.department || 'N/A'}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-bold ${
                      user.risk_level === 'critical' ? 'text-red-400' :
                      user.risk_level === 'high' ? 'text-orange-400' :
                      user.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                    }`}>{user.risk_score?.toFixed(1)}</p>
                    <p className="text-[10px] text-gray-500 uppercase">{user.risk_level}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        {/* Security Scorecard */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="cyber-card"
        >
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Eye className="w-4 h-4 text-cyber-glow" />
            Security Posture
          </h3>
          {scorecard && (
            <div className="space-y-4">
              {/* Overall Score */}
              <div className="text-center p-4 bg-cyber-dark rounded-lg border border-cyber-border">
                <p className="text-4xl font-bold text-cyber-glow">{scorecard.overall_score}</p>
                <p className="text-xs text-gray-400 mt-1">Overall Security Score</p>
              </div>

              {/* Score Breakdown */}
              {[
                { label: 'Access Control', value: scorecard.access_control_score },
                { label: 'Monitoring Coverage', value: scorecard.monitoring_coverage },
                { label: 'Response Readiness', value: scorecard.response_readiness },
                { label: 'Compliance', value: scorecard.compliance_score },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{item.label}</span>
                    <span className="text-gray-300">{item.value}%</span>
                  </div>
                  <div className="w-full h-2 bg-cyber-dark rounded-full overflow-hidden">
                    <div
                      className="h-full bg-cyber-glow rounded-full transition-all duration-1000"
                      style={{ width: `${item.value}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
