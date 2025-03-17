# Vector Knowledge Base Authentication Guide

This document provides comprehensive guidance on authentication for the Vector Knowledge Base application, including setup, security best practices, and troubleshooting.

## Authentication Methods

The application supports two authentication methods:

1. **HTTP Basic Authentication** (Primary Method) - Simple, widely supported method that works across all modern browsers and API clients
2. **Replit Auth** (Legacy Support) - Maintained for backward compatibility

## How Authentication Works

1. When a user attempts to access a protected endpoint, they will be prompted for credentials if not already authenticated
2. Credentials are verified against environment variables set in Replit Secrets
3. Upon successful authentication, a session is created to maintain the user's authenticated state
4. Future requests use the session for authentication

## Required Environment Variables

The authentication system requires the following environment variables to be set:

| Variable Name | Description |
|---------------|-------------|
| `BASIC_AUTH_USERNAME` | The username for HTTP Basic Authentication |
| `BASIC_AUTH_PASSWORD` | The password for HTTP Basic Authentication |
| `SESSION_SECRET` | A random secret key used to encrypt session data |

## Setting Up Authentication

### For Development Environment

1. Default credentials are provided for convenience in development:
   - Username: `admin`
   - Password: `changeme123`
   
   **Important:** These credentials should **never** be used in production.

2. To customize, add the required environment variables to your Replit workspace:
   - In the Replit UI, navigate to the "Secrets" tab in the Tools panel
   - Add each of the required environment variables with appropriate values:
     - Key: `BASIC_AUTH_USERNAME` | Value: Your desired username
     - Key: `BASIC_AUTH_PASSWORD` | Value: Your secure password
     - Key: `SESSION_SECRET` | Value: A random string (at least 32 characters recommended)

### For Production Deployment

1. Add the same environment variables to your Replit deployment environment:
   - Navigate to your deployment
   - Click on the three dots menu (⋮) in the top-right corner
   - Select "Deployment Settings"
   - Add the same environment variables that you set in your development environment
   - **Important:** Deployment secrets are managed separately from development secrets

## Syncing Secrets Between Development and Deployment

Replit requires secrets to be added to both environments separately. There is no automatic synchronization between development and deployment secrets.

To ensure consistency between environments:
1. Make note of all secrets in your development environment
2. Manually add the same secrets to your deployment environment
3. If a deployment shows "secrets out of sync," it means you need to update the secrets in your deployment environment

For more details on secrets management, see the [Replit Secrets Guide](replit_secrets_guide.md).

## Authentication Endpoints

- **Login**: `/login` - Form-based login page
- **Logout**: `/logout` - Clears the session and logs out the user

## Security Best Practices

1. **Use Strong Credentials**: Complex username and password combinations
2. **Change Secrets Regularly**: Rotate your secrets periodically
3. **HTTPS Only**: Ensure your deployment uses HTTPS to protect credentials
4. **Session Security**: Use a complex, random string for `SESSION_SECRET`
5. **No Hardcoding**: Never hardcode credentials in the codebase
6. **Secure Sharing**: Avoid sharing credentials in unsecured channels
7. **Audit Logs**: Review authentication logs for suspicious activity

## Troubleshooting Authentication Issues

### Common Issues in Production

1. **Authentication Failures**:
   - Verify Replit Secrets are properly set in both development and deployment environments
   - Check logs for environment variable availability
   - Ensure the application has been restarted after setting new secrets

2. **Session Issues**:
   - Clear browser cookies if experiencing session problems
   - Verify `SESSION_SECRET` is set and consistent

3. **Common Error Messages**:
   - `BASIC_AUTH_USERNAME is MISSING in production environment`: The username environment variable is not set
   - `BASIC_AUTH_PASSWORD is MISSING in production environment`: The password environment variable is not set
   - `SESSION_SECRET environment variable not set`: The session secret is missing

### Debugging

- Application logs include detailed authentication diagnostics (with sensitive information filtered out)
- Check for "Authentication failed" messages in the logs

## Implementation Details

The authentication system is implemented in the `web/http_auth.py` module, which provides:

- `http_auth_required` decorator for protecting routes
- Session management functions
- Detailed logging for troubleshooting

This implementation is designed to be simple, reliable, and compatible with the Replit environment.

## Related Documentation

- [API Specification](api_specification.md) - Learn how authentication is used in the API
- [Replit Secrets Guide](replit_secrets_guide.md) - Detailed guide on managing secrets
- [Privacy Controls](privacy_controls.md) - How sensitive authentication data is protected