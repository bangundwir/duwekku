# API Reference

Dokumentasi lengkap API endpoints untuk Admin Dashboard.

## Base URL

```
http://localhost:8080/api/admin
```

## Authentication

Semua endpoint (kecuali login) memerlukan header:
```
Authorization: Bearer <token>
```

---

## Auth Endpoints

### POST /login
Login dan dapatkan session token.

**Request:**
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response:**
```json
{
  "token": "abc123...",
  "username": "admin",
  "message": "Login successful"
}
```

### POST /logout
Logout dan invalidate session.

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

### GET /session
Cek validitas session.

**Response:**
```json
{
  "valid": true,
  "username": "admin",
  "expires_at": "2025-12-04T10:00:00"
}
```

---

## User Endpoints

### GET /users
Dapatkan daftar user dengan pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Halaman |
| per_page | int | 20 | Item per halaman |
| search | string | - | Cari username/ID |

**Response:**
```json
{
  "items": [
    {
      "user_id": 123456,
      "username": "john",
      "first_name": "John",
      "registered_at": "2025-01-01T00:00:00",
      "last_active": "2025-12-03T10:00:00",
      "is_blocked": false,
      "hourly_query_limit": 20,
      "hourly_queries_used": 5,
      "daily_query_limit": 100,
      "daily_queries_used": 25,
      "monthly_query_limit": 1000,
      "monthly_queries_used": 150,
      "total_queries": 500
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "total_pages": 5
}
```

### GET /users/{user_id}
Dapatkan detail user.

**Response:**
```json
{
  "user": { ... },
  "subscription": {
    "id": 1,
    "plan_name": "Premium",
    "start_date": "2025-12-01",
    "end_date": "2025-12-31",
    "status": "active",
    "days_remaining": 28
  }
}
```

### PUT /users/{user_id}/block
Blokir user.

**Response:**
```json
{
  "message": "User 123456 blocked",
  "is_blocked": true
}
```

### PUT /users/{user_id}/unblock
Unblock user.

**Response:**
```json
{
  "message": "User 123456 unblocked",
  "is_blocked": false
}
```

### DELETE /users/{user_id}
Hapus user dan semua data.

**Response:**
```json
{
  "message": "User 123456 deleted"
}
```

### POST /users/{user_id}/reset
Reset data user (transaksi & langganan).

**Response:**
```json
{
  "message": "User 123456 data reset successfully",
  "deleted": {
    "transactions_deleted": 50,
    "subscriptions_deleted": 3
  }
}
```

---

## Query Limit Endpoints

### PUT /users/{user_id}/limits
Set query limits user.

**Request:**
```json
{
  "hourly_limit": 20,
  "daily_limit": 100,
  "monthly_limit": 1000,
  "reset_hours": 1
}
```

**Response:**
```json
{
  "message": "Limits updated",
  "hourly_limit": 20,
  "daily_limit": 100,
  "monthly_limit": 1000,
  "reset_hours": 1
}
```

### GET /users/{user_id}/usage
Dapatkan statistik usage user.

**Response:**
```json
{
  "hourly_used": 5,
  "hourly_limit": 20,
  "hourly_remaining": 15,
  "daily_used": 25,
  "daily_limit": 100,
  "daily_remaining": 75,
  "monthly_used": 150,
  "monthly_limit": 1000,
  "monthly_remaining": 850,
  "total_queries": 500
}
```

### POST /users/{user_id}/reset-queries
Reset query counters user.

**Query Parameters:**
| Param | Type | Values | Description |
|-------|------|--------|-------------|
| reset_type | string | hourly, daily, monthly, all | Tipe reset |

**Response:**
```json
{
  "success": true,
  "message": "Query counters reset (all)",
  "reset_type": "all",
  "reset_at": "2025-12-03T10:00:00"
}
```

---

## Subscription Plan Endpoints

### GET /plans
Dapatkan semua subscription plans.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Free",
    "hourly_query_limit": 5,
    "daily_query_limit": 10,
    "monthly_query_limit": 100,
    "reset_hours": 1,
    "price": 0,
    "duration_days": 0,
    "features": ["5 query/jam", "10 query/hari"],
    "is_active": true,
    "is_default": true
  }
]
```

### GET /plans/default
Dapatkan default plan.

**Response:**
```json
{
  "id": 1,
  "name": "Free",
  ...
}
```

### POST /plans
Buat plan baru.

**Request:**
```json
{
  "name": "Premium",
  "hourly_query_limit": 50,
  "daily_query_limit": 200,
  "monthly_query_limit": 2000,
  "reset_hours": 1,
  "price": 75000,
  "duration_days": 30,
  "features": ["Export CSV", "Analisis lengkap"],
  "is_default": false
}
```

### PUT /plans/{plan_id}
Update plan.

**Request:** Sama dengan POST /plans

### PUT /plans/{plan_id}/default
Set plan sebagai default.

**Response:**
```json
{
  "message": "Plan 2 set as default"
}
```

### DELETE /plans/{plan_id}
Hapus plan.

**Response:**
```json
{
  "message": "Plan 2 deleted"
}
```

---

## User Subscription Endpoints

### PUT /users/{user_id}/subscription
Assign subscription ke user.

**Request:**
```json
{
  "plan_id": 2,
  "duration_days": 30
}
```

**Response:**
```json
{
  "message": "Subscription assigned",
  "subscription": {
    "id": 1,
    "plan_name": "Premium",
    "start_date": "2025-12-03",
    "end_date": "2026-01-02",
    "status": "active"
  }
}
```

---

## Analytics Endpoints

### GET /stats
Dapatkan statistik dashboard.

**Response:**
```json
{
  "total_users": 100,
  "active_users": 85,
  "blocked_users": 5,
  "active_subscriptions": 30,
  "today_queries": 500,
  "total_transactions": 10000
}
```

### GET /analytics/queries
Dapatkan data query harian.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| days | int | 30 | Jumlah hari |

**Response:**
```json
{
  "data": [
    {"date": "2025-12-01", "count": 150},
    {"date": "2025-12-02", "count": 200},
    {"date": "2025-12-03", "count": 175}
  ],
  "days": 30
}
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authorization header required"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid reset_type. Use: hourly, daily, monthly, or all"
}
```
