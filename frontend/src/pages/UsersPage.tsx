/**
 * Users Page
 * ============
 * User management interface for administrators.
 * Displays user list with role, department, and risk information.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Users, Search, Shield, RefreshCw, UserCheck, UserX } from 'lucide-react';
import { usersApi } from '../services/api';
import type { UserSummary } from '../types';

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'bg-red-500/20 text-red-400 border-red-500/30',
  security_analyst: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  admin: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  viewer: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  employee: 'bg-green-500/20 text-green-400 border-green-500/30',
};

export default function UsersPage() {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, page_size: 20 };
      if (searchTerm) params.search = searchTerm;
      const data = await usersApi.list(params);
      setUsers(data.data || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-cyber-glow" />
            User Management
          </h1>
          <p className="text-sm text-gray-400 mt-1">{total} registered users</p>
        </div>
        <button onClick={loadUsers} className="cyber-button flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Search */}
      <div className="cyber-card">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text" placeholder="Search by name, username, or email..." value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            className="bg-cyber-dark border border-cyber-border rounded-lg px-3 py-1.5 text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-cyber-glow/50 flex-1"
          />
        </div>
      </div>

      {/* User Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyber-glow mx-auto mb-3"></div>
          <p className="text-sm text-gray-400">Loading users...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {users.map((user, i) => (
            <motion.div
              key={user.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
              className="cyber-card-hover"
            >
              <div className="flex items-start gap-4">
                {/* Avatar */}
                <div className="w-12 h-12 bg-cyber-glow/20 rounded-xl flex items-center justify-center border border-cyber-glow/30 flex-shrink-0">
                  <span className="text-sm font-bold text-cyber-glow">
                    {user.full_name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-white truncate">{user.full_name}</h3>
                    {user.is_active ? (
                      <UserCheck className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />
                    ) : (
                      <UserX className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-gray-400 truncate">{user.username}</p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase border ${
                      ROLE_COLORS[user.role_name || ''] || 'bg-gray-500/20 text-gray-400'
                    }`}>
                      {user.role_name || 'N/A'}
                    </span>
                    {user.department_name && (
                      <span className="text-[10px] text-gray-500">{user.department_name}</span>
                    )}
                  </div>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-cyber-border">
                    <div>
                      <p className="text-[10px] text-gray-500">Risk Level</p>
                      <p className={`text-xs font-semibold uppercase ${
                        user.risk_level === 'high' || user.risk_level === 'critical' ? 'text-red-400' :
                        user.risk_level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                      }`}>{user.risk_level || 'low'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-gray-500">Last Login</p>
                      <p className="text-xs text-gray-400">
                        {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`w-8 h-8 rounded-lg text-sm font-medium transition-all ${
                p === page ? 'bg-cyber-glow text-white' : 'bg-cyber-dark text-gray-400 hover:bg-cyber-border'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
