/**
 * Sidebar Component
 * ==================
 * Left sidebar navigation for the SOC dashboard.
 * Displays navigation links with icons and active state highlighting.
 */

import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard, Shield, Activity, AlertTriangle,
  Users, Key, LogOut, ChevronRight, Zap,
} from 'lucide-react';

/**
 * Navigation items configuration.
 * Each item defines the route, label, icon, and required role.
 */
const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/alerts', label: 'Alerts', icon: AlertTriangle },
  { path: '/activities', label: 'Activity Logs', icon: Activity },
  { path: '/risk', label: 'Risk Analysis', icon: Shield },
  { path: '/users', label: 'Users', icon: Users },
  { path: '/quantum', label: 'Quantum-Safe', icon: Key },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-cyber-card border-r border-cyber-border flex flex-col z-50">
      {/* Logo Section */}
      <div className="p-6 border-b border-cyber-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cyber-glow/20 rounded-xl flex items-center justify-center border border-cyber-glow/30">
            <Shield className="w-6 h-6 text-cyber-glow" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">SentinelAI</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">Threat Detection</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <p className="text-[10px] text-gray-500 uppercase tracking-widest px-3 mb-3">Navigation</p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-cyber-glow/15 text-cyber-glow border border-cyber-glow/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-cyber-glow' : 'text-gray-500 group-hover:text-gray-300'}`} />
              <span className="text-sm font-medium">{item.label}</span>
              {isActive && <ChevronRight className="w-4 h-4 ml-auto text-cyber-glow/60" />}
            </NavLink>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="px-4 py-3 mx-4 mb-2 bg-cyber-dark rounded-lg border border-cyber-border">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-4 h-4 text-cyber-green" />
          <span className="text-xs text-gray-400">System Status</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyber-green animate-pulse"></div>
          <span className="text-xs text-cyber-green font-medium">All Systems Operational</span>
        </div>
      </div>

      {/* User Profile & Logout */}
      <div className="p-4 border-t border-cyber-border">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 bg-cyber-glow/20 rounded-full flex items-center justify-center border border-cyber-glow/30">
            <span className="text-sm font-bold text-cyber-glow">
              {user?.full_name?.split(' ').map(n => n[0]).join('') || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-[11px] text-gray-500 truncate">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
