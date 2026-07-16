"""
Integration Tests for API Endpoints
=====================================

Tests the full HTTP request/response cycle for key API endpoints
using FastAPI's TestClient.
"""

import pytest
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))


class TestHealthEndpoints:
    """Tests for application health and root endpoints."""

    def test_health_check(self):
        """Test that the health endpoint returns healthy status."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_root_endpoint(self):
        """Test that the root endpoint returns app info."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "SentinelAI"
        assert "version" in data
        assert "docs" in data


class TestAuthFlow:
    """Integration tests for the complete authentication flow."""

    def setup_method(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_login_success_with_valid_credentials(self):
        """Test login flow returns tokens on valid credentials."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert "user" in data
        assert data["user"]["username"] == "admin"

    def test_login_failure_wrong_password(self):
        """Test login fails with incorrect password."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "WrongPassword123!",
        })
        assert response.status_code == 401

    def test_login_failure_nonexistent_user(self):
        """Test login fails for non-existent user."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": "SomePassword1!",
        })
        assert response.status_code == 401

    def test_get_current_user(self):
        """Test that /me endpoint returns user info with valid token."""
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        token = login_response.json()["access_token"]

        me_response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["username"] == "admin"

    def test_get_current_user_no_token(self):
        """Test that /me fails without authentication."""
        response = self.client.get("/api/v1/auth/me")
        assert response.status_code in [401, 403]

    def test_get_current_user_invalid_token(self):
        """Test that /me fails with an invalid token."""
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code in [401, 403]

    def test_refresh_token_flow(self):
        """Test that refresh token generates a new access token."""
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = self.client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_invalid_token(self):
        """Test that refresh fails with an invalid refresh token."""
        response = self.client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.refresh.token",
        })
        assert response.status_code == 401

    def test_logout_flow(self):
        """Test complete login -> access -> logout flow."""
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        token = login_response.json()["access_token"]

        logout_response = self.client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == 200

    def test_soc_analyst_login(self):
        """Test that SOC analyst can login successfully."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "soc_analyst_1",
            "password": "Analyst@123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "security_analyst"


class TestDashboardEndpoints:
    """Integration tests for dashboard API endpoints."""

    def setup_method(self):
        """Set up test client with authenticated token."""
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_dashboard_summary(self):
        """Test that dashboard summary returns aggregated metrics."""
        response = self.client.get(
            "/api/v1/dashboard/summary",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_activities_today" in data
        assert "total_alerts_open" in data

    def test_dashboard_timeline(self):
        """Test that dashboard timeline returns chart data."""
        response = self.client.get(
            "/api/v1/dashboard/timeline?days=7",
            headers=self.headers,
        )
        assert response.status_code == 200

    def test_dashboard_recent_activity(self):
        """Test that recent activity returns a list."""
        response = self.client.get(
            "/api/v1/dashboard/recent-activity",
            headers=self.headers,
        )
        assert response.status_code == 200

    def test_dashboard_scorecard(self):
        """Test that scorecard returns posture data."""
        response = self.client.get(
            "/api/v1/dashboard/scorecard",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data

    def test_dashboard_requires_auth(self):
        """Test that dashboard endpoints require authentication."""
        response = self.client.get("/api/v1/dashboard/summary")
        assert response.status_code in [401, 403]


class TestAlertEndpoints:
    """Integration tests for alert API endpoints."""

    def setup_method(self):
        """Set up test client with authenticated token."""
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_alerts(self):
        """Test that alerts list endpoint returns data."""
        response = self.client.get(
            "/api/v1/alerts/",
            headers=self.headers,
        )
        assert response.status_code == 200

    def test_alert_stats(self):
        """Test that alert stats endpoint returns metrics."""
        response = self.client.get(
            "/api/v1/alerts/stats",
            headers=self.headers,
        )
        assert response.status_code == 200

    def test_alerts_requires_auth(self):
        """Test that alert endpoints require authentication."""
        response = self.client.get("/api/v1/alerts/")
        assert response.status_code in [401, 403]


class TestUserEndpoints:
    """Integration tests for user management API endpoints."""

    def setup_method(self):
        """Set up test client with authenticated admin token."""
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_users(self):
        """Test that users list endpoint returns data."""
        response = self.client.get(
            "/api/v1/users/",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) > 0

    def test_users_requires_auth(self):
        """Test that user endpoints require authentication."""
        response = self.client.get("/api/v1/users/")
        assert response.status_code in [401, 403]


class TestQuantumEndpoints:
    """Integration tests for quantum-safe crypto endpoints."""

    def setup_method(self):
        """Set up test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)
        login_response = self.client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "Admin@12345!",
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_quantum_info(self):
        """Test that quantum info endpoint returns algorithm details."""
        response = self.client.get(
            "/api/v1/quantum/info",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "algorithm" in data or "mode" in data
