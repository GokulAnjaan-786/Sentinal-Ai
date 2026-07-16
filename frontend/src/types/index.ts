/**
 * TypeScript Type Definitions
 * ============================
 * Central type definitions for the SentinelAI frontend application.
 * These types mirror the backend API schemas for type-safe API communication.
 */

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  department: string | null;
  is_active: boolean;
}

export interface UserSummary {
  id: string;
  username: string;
  full_name: string;
  role_name: string | null;
  department_name: string | null;
  is_active: boolean;
  risk_level: string;
  last_login: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  requires_password_change: boolean;
}

export interface Activity {
  id: string;
  user_id: string;
  username?: string;
  session_id?: string;
  activity_type: string;
  description: string | null;
  ip_address: string | null;
  location: string | null;
  device_id: string | null;
  resource_accessed: string | null;
  resource_type: string | null;
  severity: string;
  risk_contribution: number;
  status: string;
  metadata_json?: Record<string, unknown>;
  created_at: string;
}

export interface Alert {
  id: string;
  user_id: string;
  username?: string;
  alert_type: string;
  title: string;
  description: string | null;
  severity: string;
  priority: string;
  status: string;
  risk_score: number | null;
  explanation: string | null;
  recommended_action: string | null;
  source: string;
  metadata_json?: Record<string, unknown>;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_notes?: string;
  is_false_positive: boolean;
  created_at: string;
  updated_at: string;
}

export interface RiskScore {
  id: string;
  user_id: string;
  username?: string;
  score: number;
  risk_level: string;
  factors?: RiskFactor[];
  explanation?: string;
  rule_violations: number;
  calculated_at: string;
}

export interface RiskFactor {
  name: string;
  description: string;
  risk_points: number;
}

export interface DashboardSummary {
  total_users: number;
  active_users: number;
  active_sessions: number;
  total_alerts_today: number;
  critical_alerts: number;
  high_alerts: number;
  medium_alerts: number;
  low_alerts: number;
  total_activities_today: number;
  average_risk_score: number;
  users_at_risk: number;
  users_critical: number;
  threats_detected_today: number;
  system_health: string;
}

export interface ThreatTimeline {
  timestamps: string[];
  critical_counts: number[];
  high_counts: number[];
  medium_counts: number[];
  low_counts: number[];
  total_counts: number[];
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  success: boolean;
  message: string;
  error_code?: string;
}

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical';
export type AlertStatus = 'generated' | 'acknowledged' | 'investigating' | 'resolved' | 'false_positive';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
