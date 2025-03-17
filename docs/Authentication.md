# Authentication Guide

This document provides guidance on authentication for the PDF Knowledge Base application.

## Authentication Methods

The application supports two authentication methods:

1. **HTTP Basic Authentication** (Primary Method)
2. **Replit Auth** (Legacy Support)

## HTTP Basic Authentication

HTTP Basic Authentication is used for all routes in both development and production environments.

### Configuration

#### Development Environment

In development, default credentials are provided for convenience:
- Username: `admin`
- Password: `changeme123`

These credentials should **never** be used in production.

#### Production Environment (Replit Deployment)

For production deployments, you must set the following secrets in **Replit Secrets**:

1. `BASIC_AUTH_USERNAME`: Your secure username
2. `BASIC_AUTH_PASSWORD`: Your strong password
3. `SESSION_SECRET`: A random string for secure session management

### How to Set Replit Secrets

1. Navigate to the Replit project dashboard
2. Click on "Secrets" in the tools panel
3. Add each secret key-value pair:
   - Key: `BASIC_AUTH_USERNAME` | Value: Your desired username
   - Key: `BASIC_AUTH_PASSWORD` | Value: Your secure password
   - Key: `SESSION_SECRET` | Value: A random string (at least 32 characters recommended)

### Session Management

Once authenticated, a session is created to avoid requiring credentials for each request. Sessions expire after 24 hours or when the user logs out.

## Authentication Endpoints

- **Login**: `/login` - Form-based login page
- **Logout**: `/logout` - Clears the session and logs out the user

## Authentication Flow

1. User navigates to any protected route
2. If not authenticated, redirected to login page or prompted for HTTP Basic Auth credentials
3. Upon successful authentication, a session is created
4. Future requests use the session for authentication

## Security Recommendations

1. **Use Strong Credentials**: Complex username and password combinations
2. **Change Secrets Regularly**: Rotate your secrets periodically
3. **HTTPS Only**: Ensure your deployment uses HTTPS to protect credentials
4. **Audit Logs**: Review authentication logs for suspicious activity

## Troubleshooting

### Common Issues in Production

1. **Authentication Failures**:
   - Verify Replit Secrets are properly set
   - Check logs for environment variable availability
   - Ensure the application has been restarted after setting new secrets

2. **Session Issues**:
   - Clear browser cookies if experiencing session problems
   - Verify `SESSION_SECRET` is properly set

### Logging

Authentication events are logged to help with troubleshooting. Check the application logs for detailed information about authentication attempts and environment variable availability.