/**
 * Activities Page
 * =================
 * Activity log viewer with filtering, search, and pagination.
 * Displays all user activities monitored by the SentinelAI system.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Activity, Search, RefreshCw, Clock, Filter } from 'lucide-react';
import { activitiesApi } from '../services/api';
import type { Activity as ActivityType } from '../types';

const TYPE_ICONS: Record<string, string> = {
  login: '🔑', logout: '🚪', database_access: '🗄️', database_export: '📤',
  file_download: '⬇️', file_upload: '⬆️', usb_insertion: '💾', usb_removal: '💾',
  password_change: '🔒', config_change: '⚙️', email_send: '📧', email_receive: '📥',
  admin_command: '⚡', privilege_escalation: '🔺', access_denied: '🚫',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'text-red-400', high: 'text-orange-400',
  medium: 'text-yellow-400', low: 'text-green-400', info: 'text-gray-400',
};

export default function ActivitiesPage() {
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const loadActivities = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (filterType) params.activity_type = filterType;
      if (filterSeverity) params.severity = filterSeverity;
      if (searchTerm) params.search = searchTerm;
      const data = await activitiesApi.list(params);
      setActivities(data.data || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load activities:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filterType, filterSeverity, searchTerm]);

  useEffect(() => { loadActivities(); }, [loadActivities]);

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-cyber-glow" />
            Activity Logs
          </h1>
          <p className="text-sm text-gray-400 mt-1">{total} activities recorded</p>
        </div>
        <button onClick={loadActivities} className="cyber-button flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="cyber-card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-gray-500" />
            <input
              type="text" placeholder="Search activities..." value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-cyber-glow/50 w-48"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
            className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none"
          >
            <option value="">All Types</option>
            {Object.keys(TYPE_ICONS).map((t) => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <select
            value={filterSeverity}
            onChange={(e) => { setFilterSeverity(e.target.value); setPage(1); }}
            className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
        </div>
      </div>

      {/* Activity Table */}
      <div className="cyber-card overflow-hidden">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyber-glow mx-auto mb-3"></div>
            <p className="text-sm text-gray-400">Loading activities...</p>
          </div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No activities found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-cyber-border">
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">Type</th>
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">Description</th>
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">Severity</th>
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">Status</th>
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">IP Address</th>
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">Location</th>
                  <th className="text-left text-[11px] text-gray-500 uppercase tracking-wider px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((activity, i) => (
                  <motion.tr
                    key={activity.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-cyber-border/50 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-base">{TYPE_ICONS[activity.activity_type] || '📋'}</span>
                        <span className="text-xs text-gray-300 font-medium">{activity.activity_type.replace(/_/g, ' ')}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400 max-w-xs truncate">{activity.description || '-'}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium uppercase ${SEVERITY_COLORS[activity.severity] || 'text-gray-400'}`}>
                        {activity.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        activity.status === 'success' ? 'bg-green-500/20 text-green-400' :
                        activity.status === 'failure' ? 'bg-red-500/20 text-red-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {activity.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400 font-mono">{activity.ip_address || '-'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400">{activity.location || '-'}</td>
                    <td className="px-4 py-3 text-xs text-gray-400">
                      {activity.created_at ? new Date(activity.created_at).toLocaleString() : '-'}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-cyber-border">
            <p className="text-xs text-gray-500">
              Page {page} of {totalPages} ({total} total)
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-xs bg-cyber-dark border border-cyber-border rounded text-gray-400 hover:text-white disabled:opacity-30"
              >
                Prev
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-xs bg-cyber-dark border border-cyber-border rounded text-gray-400 hover:text-white disabled:opacity-30"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
