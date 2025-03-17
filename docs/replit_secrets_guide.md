# Managing Secrets in Replit Environments

This guide provides specific instructions for handling secrets in the Replit environment, focusing on the unique challenges of syncing secrets between development and deployment.

## Understanding Replit Secrets

Replit manages secrets in two separate environments:

1. **Development Environment** - Your main workspace where you develop and test code
2. **Deployment Environment** - The production environment where your deployed application runs

**Important:** Secrets do not automatically sync between these environments.

## Required Secrets for Vector Knowledge Base

The Vector Knowledge Base application requires these secrets:

| Secret Name | Purpose |
|-------------|---------|
| `SESSION_SECRET` | Used for securing user sessions |
| `BASIC_AUTH_USERNAME` | Username for HTTP Basic Authentication |
| `BASIC_AUTH_PASSWORD` | Password for HTTP Basic Authentication |
| `OPENAI_API_KEY` | API key for OpenAI integration |
| `VKB_API_KEY` | Application-specific API key (if used) |

## Adding Secrets to Development Environment

1. Open your Replit workspace
2. Click on the "Tools" tab in the sidebar
3. Select "Secrets"
4. Click "Add a new secret"
5. Enter the secret name and value
6. Repeat for each required secret

## Adding Secrets to Deployment Environment

1. Go to your deployment page
2. Click the three-dot menu (⋮) in the top right corner
3. Select "Deployment Settings"
4. Find the "Secrets" or "Environment Variables" section
5. Add each secret with the same name and value as in your development environment
6. Save your changes
7. Redeploy your application for the changes to take effect

## Checking for "Out of Sync" Secrets

When a deployment shows "5 secrets out of sync" or similar message:

1. This indicates that your deployment environment is missing secrets that exist in your development environment
2. Follow the steps above to add the missing secrets to your deployment environment
3. Redeploy the application

## Best Practices

1. **Maintain a Secrets Inventory** - Keep a secure record of all secrets used in your application
2. **Use Consistent Names** - Use the same secret names in both environments
3. **Redeploy After Changes** - Always redeploy after updating secrets
4. **Regular Audits** - Periodically check that both environments have the same secrets
5. **Update Both Environments** - When changing a secret, remember to update it in both places

## Troubleshooting

If your application shows authentication issues after deployment:

1. Check if your deployment shows "secrets out of sync"
2. Verify that all required secrets are present in the deployment environment
3. Ensure the values match exactly between environments
4. Check application logs for specific error messages about missing secrets
5. Redeploy the application after making changes to secrets

## Security Notes

1. Never share your secrets in public repositories or discussions
2. Rotate secrets periodically according to your security policies
3. Use strong, unique values for passwords and API keys
4. Limit access to who can view and modify secrets in both environments