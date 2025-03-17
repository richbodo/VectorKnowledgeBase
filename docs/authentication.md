# Vector Knowledge Base Authentication Guide

This document describes the authentication mechanism used in the Vector Knowledge Base application and provides instructions for system administrators and developers.

## Authentication Overview

The Vector Knowledge Base uses HTTP Basic Authentication, a simple and widely supported authentication method that works across all modern browsers and API clients. This provides a reliable and consistent authentication experience across both development and production environments.

## How It Works

1. When a user attempts to access a protected endpoint, they will be prompted for credentials if they are not already authenticated
2. Credentials are verified against environment variables set in Replit Secrets
3. Upon successful authentication, a session is created to maintain the user's authenticated state

## Required Environment Variables

The authentication system requires the following environment variables to be set:

| Variable Name | Description |
|---------------|-------------|
| `BASIC_AUTH_USERNAME` | The username for HTTP Basic Authentication |
| `BASIC_AUTH_PASSWORD` | The password for HTTP Basic Authentication |
| `SESSION_SECRET` | A random secret key used to encrypt session data |

## Setting Up Authentication

### For Development

1. Add the required environment variables to your Replit workspace:
   - In the Replit UI, navigate to the "Secrets" tab in the Tools panel
   - Add each of the required environment variables with appropriate values
   - Ensure the values are secure (use a strong password and a random session secret)

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

## Troubleshooting Authentication Issues

If you encounter authentication issues:

1. **Common Issues**:
   - Credentials not being accepted: Verify that the environment variables are set correctly in both development and deployment environments
   - Session not persisting: Check that the SESSION_SECRET is set and consistent

2. **Debugging**:
   - Application logs include detailed authentication diagnostics (with sensitive information filtered out)
   - Check for "Authentication failed" messages in the logs

3. **Error Messages**:
   - `BASIC_AUTH_USERNAME is MISSING in production environment`: The username environment variable is not set
   - `BASIC_AUTH_PASSWORD is MISSING in production environment`: The password environment variable is not set
   - `SESSION_SECRET environment variable not set`: The session secret is missing

## Security Best Practices

1. Use strong, unique passwords for the `BASIC_AUTH_PASSWORD`
2. Use a complex, random string for `SESSION_SECRET`
3. Change credentials periodically
4. Never hardcode credentials in the codebase
5. Avoid sharing credentials in unsecured channels

## Implementation Details

The authentication system is implemented in the `web/http_auth.py` module, which provides:

- `http_auth_required` decorator for protecting routes
- Session management functions
- Detailed logging for troubleshooting

This implementation is designed to be simple, reliable, and compatible with the Replit environment.