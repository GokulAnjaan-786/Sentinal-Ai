/**
 * App Component
 * ===============
 * Root application component with routing configuration.
 * Defines all application routes and layout structure.
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import AlertsPage from './pages/AlertsPage';
import ActivitiesPage from './pages/ActivitiesPage';
import RiskAnalysisPage from './pages/RiskAnalysisPage';
import UsersPage from './pages/UsersPage';
import QuantumPage from './pages/QuantumPage';

/**
 * Protected route wrapper that redirects to login if not authenticated.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-cyber-darker flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-glow"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="alerts" element={<AlertsPage />} />
        <Route path="activities" element={<ActivitiesPage />} />
        <Route path="risk" element={<RiskAnalysisPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="quantum" element={<QuantumPage />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
