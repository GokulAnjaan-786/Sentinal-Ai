/**
 * Risk Analysis Page
 * ====================
 * Risk score analysis and visualization for user behavior monitoring.
 * Displays risk trends, top risk users, and risk factor breakdowns.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend,
} from 'recharts';
import { riskApi, dashboardApi } from '../services/api';

export default function RiskAnalysisPage() {
  const [topRisk, setTopRisk] = useState<any[]>([]);
  const [deptRisk, setDeptRisk] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [userTrend, setUserTrend] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [riskRes, deptRes] = await Promise.allSettled([
        riskApi.getTopRisk(15),
        dashboardApi.getDepartmentRisk(),
      ]);
      if (riskRes.status === 'fulfilled') setTopRisk(riskRes.value.top_risk_users || []);
      if (deptRes.status === 'fulfilled') setDeptRisk(deptRes.value || []);
    } catch (err) {
      console.error('Failed to load risk data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = async (user: any) => {
    setSelectedUser(user);
    try {
      const trend = await riskApi.getTrend(user.user_id);
      setUserTrend(trend);
    } catch {}
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-400 bg-red-500/20 border-red-500/30';
      case 'high': return 'text-orange-400 bg-orange-500/20 border-orange-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      default: return 'text-green-400 bg-green-500/20 border-green-500/30';
    }
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'increasing') return <TrendingUp className="w-4 h-4 text-red-400" />;
    if (trend === 'decreasing') return <TrendingDown className="w-4 h-4 text-green-400" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-glow"></div>
      </div>
    );
  }

  // Prepare department chart data
  const deptChartData = deptRisk.map((d: any) => ({
    name: d.department_code,
    avgRisk: d.average_risk_score,
    maxRisk: d.max_risk_score,
    users: d.user_count,
  }));

  // Prepare user trend chart data
  const trendChartData = userTrend?.scores?.map((score: number, i: number) => ({
    point: i + 1,
    score: score,
  })) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-cyber-glow" />
          Risk Analysis
        </h1>
        <p className="text-sm text-gray-400 mt-1">User behavioral risk scoring and trend analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Risk Users List */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-sm font-semibold text-white mb-3">Users by Risk Score</h3>
          {topRisk.map((user, i) => (
            <motion.div
              key={user.user_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => handleUserSelect(user)}
              className={`cyber-card cursor-pointer transition-all duration-200 ${
                selectedUser?.user_id === user.user_id ? 'border-cyber-glow/50 glow-border' : 'hover:border-gray-600'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-cyber-dark rounded-full flex items-center justify-center border border-cyber-border">
                  <span className="text-xs font-bold text-gray-400">{i + 1}</span>
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
                  }`}>
                    {user.risk_score?.toFixed(1)}
                  </p>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${getRiskColor(user.risk_level)}`}>
                    {user.risk_level}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* User Detail */}
          {selectedUser ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="cyber-card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">{selectedUser.full_name}</h3>
                  <p className="text-sm text-gray-400">{selectedUser.department} | {selectedUser.username}</p>
                </div>
                <div className="text-right">
                  <p className={`text-3xl font-bold ${
                    selectedUser.risk_level === 'critical' ? 'text-red-400' :
                    selectedUser.risk_level === 'high' ? 'text-orange-400' :
                    selectedUser.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                  }`}>{selectedUser.risk_score?.toFixed(1)}</p>
                  <p className="text-xs text-gray-500">Risk Score</p>
                </div>
              </div>

              {userTrend && (
                <div className="grid grid-cols-4 gap-4 mb-4">
                  {[
                    { label: 'Average (7d)', value: userTrend.average?.toFixed(1) || '0' },
                    { label: 'Max (30d)', value: userTrend.max?.toFixed(1) || '0' },
                    { label: 'Min (30d)', value: userTrend.min?.toFixed(1) || '0' },
                    { label: 'Trend', value: userTrend.trend || 'N/A', icon: getTrendIcon(userTrend.trend) },
                  ].map((item) => (
                    <div key={item.label} className="text-center p-3 bg-cyber-dark rounded-lg border border-cyber-border">
                      <div className="flex items-center justify-center gap-1">
                        <p className="text-sm font-bold text-white">{item.value}</p>
                        {item.icon}
                      </div>
                      <p className="text-[10px] text-gray-500 mt-1">{item.label}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Risk Trend Chart */}
              {trendChartData.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-white mb-3">Risk Score History</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={trendChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                      <XAxis dataKey="point" tick={{ fill: '#6b7280', fontSize: 11 }} />
                      <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '8px' }} />
                      <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>
          ) : (
            <div className="cyber-card text-center py-16">
              <AlertTriangle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">Select a user to view detailed risk analysis</p>
            </div>
          )}

          {/* Department Risk Chart */}
          <div className="cyber-card">
            <h3 className="text-sm font-semibold text-white mb-4">Department Risk Overview</h3>
            {deptChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={deptChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '8px' }} />
                  <Legend wrapperStyle={{ fontSize: '11px', color: '#9ca3af' }} />
                  <Bar dataKey="avgRisk" name="Avg Risk" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="maxRisk" name="Max Risk" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No department data available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
