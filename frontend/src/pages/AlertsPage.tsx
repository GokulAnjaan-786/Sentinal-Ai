/**
 * Alerts Page
 * =============
 * Security alerts management interface for SOC analysts.
 * Displays all alerts with filtering, status management, and detailed explanations.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle, Filter, CheckCircle, XCircle, Eye,
  Clock, ChevronDown, Search, RefreshCw, Bell, BellOff,
} from 'lucide-react';
import { alertsApi } from '../services/api';
import type { Alert, AlertStatus } from '../types';

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
};

const STATUS_STYLES: Record<string, string> = {
  generated: 'bg-blue-500/20 text-blue-400',
  acknowledged: 'bg-yellow-500/20 text-yellow-400',
  investigating: 'bg-purple-500/20 text-purple-400',
  resolved: 'bg-green-500/20 text-green-400',
  false_positive: 'bg-gray-500/20 text-gray-400',
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<any>(null);

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 15 };
      if (filterSeverity) params.severity = filterSeverity;
      if (filterStatus) params.status = filterStatus;
      if (searchTerm) params.search = searchTerm;

      const data = await alertsApi.list(params);
      setAlerts(data.data || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filterSeverity, filterStatus, searchTerm]);

  const loadStats = async () => {
    try {
      const data = await alertsApi.getStats(30);
      setStats(data);
    } catch {}
  };

  useEffect(() => { loadAlerts(); }, [loadAlerts]);
  useEffect(() => { loadStats(); }, []);

  const handleAcknowledge = async (alertId: string) => {
    try {
      await alertsApi.acknowledge(alertId);
      loadAlerts();
      loadStats();
      if (selectedAlert?.id === alertId) {
        setSelectedAlert({ ...selectedAlert, status: 'acknowledged' });
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (alertId: string, isFalsePositive: boolean = false) => {
    try {
      await alertsApi.resolve(alertId, undefined, isFalsePositive);
      loadAlerts();
      loadStats();
      if (selectedAlert?.id === alertId) {
        setSelectedAlert({
          ...selectedAlert,
          status: isFalsePositive ? 'false_positive' : 'resolved',
        });
      }
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const totalPages = Math.ceil(total / 15);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-cyber-glow" />
            Security Alerts
          </h1>
          <p className="text-sm text-gray-400 mt-1">{total} total alerts in system</p>
        </div>
        <button onClick={loadAlerts} className="cyber-button flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Row */}
      {stats && (
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: 'Total (30d)', value: stats.total_alerts, color: 'text-white' },
            { label: 'Critical', value: stats.alerts_by_severity?.critical || 0, color: 'text-red-400' },
            { label: 'High', value: stats.alerts_by_severity?.high || 0, color: 'text-orange-400' },
            { label: 'Medium', value: stats.alerts_by_severity?.medium || 0, color: 'text-yellow-400' },
            { label: 'Low', value: stats.alerts_by_severity?.low || 0, color: 'text-green-400' },
          ].map((item) => (
            <div key={item.label} className="cyber-card text-center py-3">
              <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
              <p className="text-[11px] text-gray-500">{item.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="cyber-card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search alerts..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-cyber-glow/50 w-48"
            />
          </div>
          <select
            value={filterSeverity}
            onChange={(e) => { setFilterSeverity(e.target.value); setPage(1); }}
            className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-cyber-glow/50"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-cyber-glow/50"
          >
            <option value="">All Statuses</option>
            <option value="generated">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="false_positive">False Positive</option>
          </select>
        </div>
      </div>

      {/* Alert List + Detail Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Alert List */}
        <div className={`space-y-3 ${selectedAlert ? 'lg:col-span-3' : 'lg:col-span-5'}`}>
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyber-glow mx-auto mb-3"></div>
              <p className="text-sm text-gray-400">Loading alerts...</p>
            </div>
          ) : alerts.length === 0 ? (
            <div className="cyber-card text-center py-12">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
              <p className="text-gray-400">No alerts matching your filters</p>
            </div>
          ) : (
            alerts.map((alert, i) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => setSelectedAlert(selectedAlert?.id === alert.id ? null : alert)}
                className={`cyber-card cursor-pointer transition-all duration-200 ${
                  selectedAlert?.id === alert.id ? 'border-cyber-glow/50 glow-border' : 'hover:border-gray-600'
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Severity Indicator */}
                  <div className={`px-2 py-1 rounded text-[10px] font-bold uppercase border ${
                    SEVERITY_STYLES[alert.severity] || 'bg-gray-500/20 text-gray-400'
                  }`}>
                    {alert.severity}
                  </div>

                  {/* Alert Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-white truncate">{alert.title}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        STATUS_STYLES[alert.status] || 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {alert.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 line-clamp-1">{alert.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-[11px] text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                      <span>Source: {alert.source}</span>
                      {alert.risk_score != null && (
                        <span className={alert.risk_score > 70 ? 'text-red-400' : alert.risk_score > 40 ? 'text-yellow-400' : 'text-gray-400'}>
                          Risk: {alert.risk_score.toFixed(1)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="flex items-center gap-2">
                    {alert.status === 'generated' && (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleAcknowledge(alert.id); }}
                        className="p-1.5 text-yellow-400 hover:bg-yellow-500/10 rounded-lg transition-all"
                        title="Acknowledge"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    )}
                    {(alert.status === 'acknowledged' || alert.status === 'investigating') && (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleResolve(alert.id); }}
                        className="p-1.5 text-green-400 hover:bg-green-500/10 rounded-lg transition-all"
                        title="Resolve"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                    p === page
                      ? 'bg-cyber-glow text-white'
                      : 'bg-cyber-dark text-gray-400 hover:bg-cyber-border'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Alert Detail Panel */}
        {selectedAlert && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2 cyber-card h-fit sticky top-24"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">Alert Details</h3>
              <button onClick={() => setSelectedAlert(null)} className="text-gray-500 hover:text-gray-300">
                <XCircle className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Title & Status */}
              <div>
                <h4 className="text-base font-semibold text-white mb-1">{selectedAlert.title}</h4>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                    SEVERITY_STYLES[selectedAlert.severity]
                  }`}>{selectedAlert.severity}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                    STATUS_STYLES[selectedAlert.status]
                  }`}>{selectedAlert.status.replace('_', ' ')}</span>
                </div>
              </div>

              {/* Description */}
              <div>
                <p className="text-[11px] text-gray-500 uppercase mb-1">Description</p>
                <p className="text-sm text-gray-300">{selectedAlert.description || 'No description'}</p>
              </div>

              {/* Explainable AI Output */}
              {selectedAlert.explanation && (
                <div className="p-3 bg-cyber-dark rounded-lg border border-cyber-border">
                  <p className="text-[11px] text-cyber-glow uppercase mb-2 font-semibold flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    AI Explanation
                  </p>
                  <p className="text-xs text-gray-300 leading-relaxed">{selectedAlert.explanation}</p>
                </div>
              )}

              {/* Recommended Action */}
              {selectedAlert.recommended_action && (
                <div className="p-3 bg-yellow-500/5 rounded-lg border border-yellow-500/20">
                  <p className="text-[11px] text-yellow-400 uppercase mb-1 font-semibold">Recommended Action</p>
                  <p className="text-xs text-gray-300">{selectedAlert.recommended_action}</p>
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="text-[10px] text-gray-500 uppercase">Source</p>
                  <p className="text-gray-300">{selectedAlert.source}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 uppercase">Risk Score</p>
                  <p className="text-gray-300">{selectedAlert.risk_score?.toFixed(1) || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 uppercase">Created</p>
                  <p className="text-gray-300">{new Date(selectedAlert.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 uppercase">Type</p>
                  <p className="text-gray-300">{selectedAlert.alert_type}</p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2 border-t border-cyber-border">
                {selectedAlert.status === 'generated' && (
                  <button
                    onClick={() => handleAcknowledge(selectedAlert.id)}
                    className="flex-1 cyber-button text-xs py-2"
                  >
                    <Eye className="w-3 h-3 mr-1 inline" /> Acknowledge
                  </button>
                )}
                {(selectedAlert.status === 'acknowledged' || selectedAlert.status === 'investigating') && (
                  <>
                    <button
                      onClick={() => handleResolve(selectedAlert.id, false)}
                      className="flex-1 cyber-button-primary text-xs py-2"
                    >
                      <CheckCircle className="w-3 h-3 mr-1 inline" /> Resolve
                    </button>
                    <button
                      onClick={() => handleResolve(selectedAlert.id, true)}
                      className="flex-1 bg-gray-500/20 text-gray-400 border border-gray-500/30 text-xs py-2 rounded-lg hover:bg-gray-500/30 transition-all"
                    >
                      <XCircle className="w-3 h-3 mr-1 inline" /> False Positive
                    </button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
