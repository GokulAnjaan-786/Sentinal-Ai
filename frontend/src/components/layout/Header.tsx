/**
 * Header Component
 * =================
 * Top header bar with search, notifications, and user actions.
 */

import { Bell, Search, Clock } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function Header() {
  const { user } = useAuth();
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 bg-cyber-card/80 backdrop-blur-sm border-b border-cyber-border flex items-center justify-between px-6 sticky top-0 z-40">
      {/* Search Bar */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search activities, alerts, users..."
            className="w-full pl-10 pr-4 py-2 bg-cyber-dark border border-cyber-border rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-cyber-glow/50 focus:ring-1 focus:ring-cyber-glow/30 transition-all"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Live Clock */}
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock className="w-4 h-4" />
          <span className="font-mono">{currentTime.toLocaleTimeString()}</span>
        </div>

        {/* Notification Bell */}
        <button className="relative p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all">
          <Bell className="w-5 h-5" />
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
            <span className="text-[9px] font-bold text-white">3</span>
          </span>
        </button>

        {/* User Avatar */}
        <div className="flex items-center gap-2 pl-4 border-l border-cyber-border">
          <div className="w-8 h-8 bg-cyber-glow/20 rounded-full flex items-center justify-center border border-cyber-glow/30">
            <span className="text-xs font-bold text-cyber-glow">
              {user?.full_name?.split(' ').map(n => n[0]).join('') || 'U'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
