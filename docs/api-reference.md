# API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints require a valid JWT Bearer token unless marked as public.

---

## Authentication

### POST /auth/login

Authenticate a user and receive tokens.

**Request:**
```json
{
  "username": "admin",
  "password": "Admin@12345!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid-here",
    "username": "admin",
    "full_name": "System Administrator",
    "role": "super_admin",
    "department": "Security Operations Center",
    "is_active": true
  }
}
```

**Errors:**
- `401`: Invalid credentials
- `403`: Account locked
- `422`: Validation error

---

### POST /auth/refresh

Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "new-access-token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### POST /auth/logout

Invalidate the current session.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /auth/me

Get the current authenticated user's profile.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid",
  "username": "admin",
  "full_name": "System Administrator",
  "email": "admin@sentinel.ai",
  "role": "super_admin",
  "department": "Security Operations Center",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Users

### GET /users

List all users (requires `users.view` permission).

**Query Parameters:**
- `page` (int, default 1): Page number
- `limit` (int, default 20): Items per page
- `role` (string): Filter by role
- `department` (string): Filter by department
- `is_active` (bool): Filter by active status

**Response (200):**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "analyst_1",
      "full_name": "Jane Smith",
      "role": "security_analyst",
      "department": "Security Operations Center",
      "is_active": true,
      "last_login": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "pages": 1
}
```

---

### GET /users/{user_id}

Get a specific user by ID.

**Response (200):** User object

---

### POST /users

Create a new user (requires `users.create` permission).

**Request:**
```json
{
  "username": "new_analyst",
  "email": "analyst@sentinel.ai",
  "full_name": "New Analyst",
  "password": "SecureP@ss1!",
  "role": "security_analyst",
  "department": "Security Operations Center"
}
```

**Response (201):** Created user object (without password)

---

### PUT /users/{user_id}

Update a user (requires `users.update` permission).

**Request:**
```json
{
  "full_name": "Updated Name",
  "role": "admin"
}
```

**Response (200):** Updated user object

---

### DELETE /users/{user_id}

Delete a user (requires `users.delete` permission).

**Response (200):**
```json
{
  "message": "User deleted successfully"
}
```

---

## Activities

### GET /activities

List activities with filtering and pagination.

**Query Parameters:**
- `page` (int, default 1)
- `limit` (int, default 50)
- `user_id` (string): Filter by user
- `activity_type` (string): Filter by type
- `severity` (string): Filter by severity
- `start_date` (datetime): Start of date range
- `end_date` (datetime): End of date range

**Response (200):**
```json
{
  "activities": [
    {
      "id": "uuid",
      "user_id": "user-uuid",
      "activity_type": "login",
      "status": "success",
      "severity": "info",
      "ip_address": "10.0.1.100",
      "location": "New York",
      "device_id": "dev_0001",
      "risk_contribution": 0.1,
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 1500,
  "page": 1
}
```

---

### POST /activities

Record a new activity (triggers detection pipeline).

**Request:**
```json
{
  "user_id": "user-uuid",
  "activity_type": "database_query",
  "status": "success",
  "ip_address": "10.0.1.100",
  "location": "New York",
  "device_id": "dev_0001",
  "details": {
    "query": "SELECT * FROM customers",
    "rows_returned": 50000
  }
}
```

**Response (201):** Created activity with detection results

---

### GET /activities/user/{user_id}

Get activity history for a specific user.

---

## Alerts

### GET /alerts

List alerts with filtering.

**Query Parameters:**
- `page` (int, default 1)
- `limit` (int, default 20)
- `severity` (string): Filter by severity (low, medium, high, critical)
- `status` (string): Filter by status (open, investigating, resolved, dismissed)
- `user_id` (string): Filter by affected user

**Response (200):**
```json
{
  "alerts": [
    {
      "id": "uuid",
      "user_id": "user-uuid",
      "alert_type": "rule_violation",
      "severity": "high",
      "status": "open",
      "title": "USB Device Usage Detected",
      "description": "Unauthorized USB device connected...",
      "risk_score": 72.5,
      "explanation": "User connected USB device during off-hours...",
      "recommended_actions": ["Investigate immediately", "Review access logs"],
      "created_at": "2024-01-15T02:30:00Z"
    }
  ],
  "total": 45,
  "page": 1
}
```

---

### GET /alerts/{alert_id}

Get a specific alert with full details.

---

### PUT /alerts/{alert_id}/status

Update an alert's status.

**Request:**
```json
{
  "status": "investigating",
  "notes": "Starting investigation into USB usage"
}
```

**Response (200):** Updated alert object

---

### GET /alerts/stats

Get alert statistics (last 24h, 7d, 30d).

**Response (200):**
```json
{
  "total_open": 12,
  "critical": 2,
  "high": 5,
  "medium": 3,
  "low": 2,
  "by_type": {
    "rule_violation": 8,
    "ml_anomaly": 3,
    "risk_threshold": 1
  }
}
```

---

## Risk Analysis

### GET /risk/score/{user_id}

Get current risk score for a user.

**Response (200):**
```json
{
  "user_id": "user-uuid",
  "score": 72.5,
  "risk_level": "high",
  "factors": [
    {
      "name": "ML Anomaly Detection",
      "risk_points": 32.0,
      "weight": 0.4,
      "description": "High anomaly score detected"
    },
    {
      "name": "Rule Violations",
      "risk_points": 18.0,
      "weight": 0.3,
      "description": "3 rules triggered"
    }
  ],
  "explanation": "Risk Score Assessment: 72.5/100 (HIGH)\n\nKey Risk Factors:\n- ML Anomaly Detection contributed 32.0 points...",
  "recommended_actions": [
    "Immediate investigation recommended",
    "Review all recent activities for this user",
    "Consider temporary access restrictions"
  ]
}
```

---

### GET /risk/trend/{user_id}

Get risk score trend for a user over time.

**Query Parameters:**
- `days` (int, default 30): Number of days to look back

---

### GET /risk/top-risky

Get the top users by risk score.

**Query Parameters:**
- `limit` (int, default 10): Number of users to return

---

## Dashboard

### GET /dashboard/overview

Get aggregated dashboard statistics.

**Response (200):**
```json
{
  "total_users": 150,
  "total_activities_today": 12500,
  "total_alerts_open": 12,
  "avg_risk_score": 28.5,
  "activities_trend": [
    {"hour": "00:00", "count": 120},
    {"hour": "01:00", "count": 45}
  ]
}
```

---

### GET /dashboard/risk-distribution

Get risk score distribution across all users.

---

### GET /dashboard/alert-timeline

Get alert volume over time.

---

### GET /dashboard/activity-feed

Get recent activity feed for the dashboard.

---

## Threat Intelligence

### GET /threats/history

Get historical threat data.

---

### GET /threats/patterns

Get detected threat patterns.

---

## Quantum-Safe Cryptography

### GET /quantum/info

Get QPC system information (algorithm details, mode).

**Response (200):**
```json
{
  "algorithm": "CRYSTALS-Kyber + CRYSTALS-Dilithium",
  "mode": "simulation",
  "oqs_available": false,
  "key_encapsulation": "ML-KEM-512",
  "digital_signature": "ML-DSA-44"
}
```

---

### POST /quantum/encrypt

Encrypt data using quantum-safe encryption.

**Request:**
```json
{
  "data": "Sensitive financial data",
  "recipient_public_key": "base64-encoded-key"
}
```

**Response (200):**
```json
{
  "ciphertext": "encrypted-base64-data",
  "algorithm": "CRYSTALS-Kyber",
  "key_id": "key-uuid"
}
```

---

### POST /quantum/sign

Sign data using quantum-safe digital signature.

**Request:**
```json
{
  "data": "Transaction authorization",
  "private_key": "base64-encoded-key"
}
```

**Response (200):**
```json
{
  "signature": "base64-signature",
  "algorithm": "CRYSTALS-Dilithium",
  "signed_at": "2024-01-15T09:00:00Z"
}
```

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (resource already exists) |
| 422 | Validation Error |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

---

## Rate Limiting

All endpoints are rate-limited to **60 requests per minute** per user.

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the window resets

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Maximum 60 requests per minute."
}
```
