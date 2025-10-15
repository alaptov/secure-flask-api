# API Testing Guide

This guide shows you how to test the API endpoints using curl or any HTTP client.

## Getting Started

1. **Start the server**
   ```bash
   python run.py
   ```

2. **Base URL**: `http://127.0.0.1:5000`

## Authentication

### 1. Login and Get API Key

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "changeme123"
  }'
```

**Response:**
```json
{
  "message": "Authentication successful",
  "api_key": "your-generated-api-key-here",
  "user": {
    "id": 1,
    "username": "admin",
    "is_admin": true,
    "created_at": "2025-10-15T00:00:00",
    "last_login": null
  },
  "expires_at": null
}
```

**Save the `api_key` from the response for subsequent requests!**

### 2. Get Current User Info

```bash
curl -X GET http://127.0.0.1:5000/api/auth/me \
  -H "X-API-Key: your-api-key-here"
```

## API Key Management

### List Your API Keys

```bash
curl -X GET http://127.0.0.1:5000/api/keys \
  -H "Cookie: session=your-session-cookie"
```

Note: This requires browser session authentication. Login through the web interface first.

### Create New API Key

```bash
curl -X POST http://127.0.0.1:5000/api/keys \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{
    "name": "My Test API Key"
  }'
```

### Revoke API Key

```bash
curl -X DELETE http://127.0.0.1:5000/api/keys/1 \
  -H "Cookie: session=your-session-cookie"
```

## User Management (Admin Only)

### List All Users

```bash
curl -X GET http://127.0.0.1:5000/api/users \
  -H "Cookie: session=your-session-cookie"
```

### Get User by ID

```bash
curl -X GET http://127.0.0.1:5000/api/users/1 \
  -H "Cookie: session=your-session-cookie"
```

### Update User

```bash
curl -X PUT http://127.0.0.1:5000/api/users/2 \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{
    "is_active": false,
    "is_admin": true
  }'
```

### Delete User

```bash
curl -X DELETE http://127.0.0.1:5000/api/users/2 \
  -H "Cookie: session=your-session-cookie"
```

## API Information

Get API documentation and available endpoints:

```bash
curl -X GET http://127.0.0.1:5000/api/
```

## Python Example

```python
import requests

# Base URL
BASE_URL = "http://127.0.0.1:5000/api"

# Login and get API key
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "username": "admin",
        "password": "changeme123"
    }
)

data = response.json()
api_key = data["api_key"]

# Use API key for subsequent requests
headers = {"X-API-Key": api_key}

# Get current user info
user_info = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(user_info.json())
```

## JavaScript Example (Fetch API)

```javascript
// Login and get API key
const login = async () => {
  const response = await fetch('http://127.0.0.1:5000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: 'admin',
      password: 'changeme123'
    })
  });

  const data = await response.json();
  return data.api_key;
};

// Use API key
const getUserInfo = async (apiKey) => {
  const response = await fetch('http://127.0.0.1:5000/api/auth/me', {
    headers: {
      'X-API-Key': apiKey
    }
  });

  const data = await response.json();
  console.log(data);
};

// Usage
login().then(apiKey => getUserInfo(apiKey));
```

## Rate Limits

Be aware of the following rate limits:

- **Default**: 200 requests per day, 50 per hour
- **Login**: 10 requests per minute
- **Registration**: 5 requests per hour
- **Password Change**: 5 requests per hour

When you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "message": "Username and password are required"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication failed",
  "message": "Invalid username or password"
}
```

### 403 Forbidden
```json
{
  "error": "Admin access required",
  "message": "You do not have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "message": "The requested resource was not found"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "message": "10 per 1 minute"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Testing with Postman

1. Import the endpoints into Postman
2. Create an environment variable for `api_key`
3. Use `{{api_key}}` in the X-API-Key header
4. Save the API key from the login response to the environment variable

## Testing Tips

1. **Save your API key**: Store it securely after login
2. **Check rate limits**: Don't make too many requests too quickly
3. **Use proper headers**: Always include Content-Type for JSON requests
4. **Handle errors**: Check response status codes
5. **Test authentication**: Try accessing protected endpoints without credentials
6. **Test authorization**: Try admin endpoints with non-admin users

## Security Testing

### Test Account Lockout
Try logging in with wrong password 5 times:

```bash
for i in {1..5}; do
  curl -X POST http://127.0.0.1:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "wrongpassword"}'
  echo "\nAttempt $i"
done
```

### Test Rate Limiting
Send multiple requests quickly:

```bash
for i in {1..15}; do
  curl -X POST http://127.0.0.1:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "changeme123"}'
  echo "\nRequest $i"
done
```

### Test CSRF Protection
Try submitting a form without CSRF token (will fail on web forms).

---

Happy Testing!
