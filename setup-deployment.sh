#!/bin/bash

# Setup script for deployment configuration
# This script helps you set up GitHub secrets for CI/CD deployment

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Flask App Deployment Setup Script                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Install it with: brew install gh"
    echo "Or visit: https://cli.github.com/"
    exit 1
fi

# Check if user is logged in to gh
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}You need to login to GitHub CLI first.${NC}"
    echo "Run: gh auth login"
    exit 1
fi

echo "This script will help you set up GitHub secrets for automated deployment."
echo ""

# Get server details
echo -e "${GREEN}Step 1: Server Configuration${NC}"
read -p "Enter your SSH server hostname or IP: " SSH_HOST
read -p "Enter your SSH username: " SSH_USER
read -p "Enter your SSH port [22]: " SSH_PORT
SSH_PORT=${SSH_PORT:-22}
read -p "Enter deployment path [/var/www]: " DEPLOY_PATH
DEPLOY_PATH=${DEPLOY_PATH:-/var/www}

echo ""
echo -e "${GREEN}Step 2: Application Configuration${NC}"
read -p "Enter admin email: " ADMIN_EMAIL

# Generate secret key
echo "Generating Flask secret key..."
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
echo -e "${GREEN}Secret key generated: ${SECRET_KEY}${NC}"

# Get admin password
read -sp "Enter admin password: " ADMIN_PASSWORD
echo ""

# SSH Key
echo ""
echo -e "${GREEN}Step 3: SSH Key Configuration${NC}"
echo "We need your SSH private key for deployment."
echo "Options:"
echo "1. Use existing SSH key"
echo "2. Generate new SSH key for deployment"
read -p "Choose option [1/2]: " SSH_KEY_OPTION

if [ "$SSH_KEY_OPTION" == "2" ]; then
    echo "Generating new SSH key..."
    ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-deploy -N ""
    echo -e "${GREEN}SSH key generated at ~/.ssh/github-deploy${NC}"
    echo ""
    echo -e "${YELLOW}IMPORTANT: Copy the public key to your server:${NC}"
    echo "ssh-copy-id -i ~/.ssh/github-deploy.pub ${SSH_USER}@${SSH_HOST}"
    echo ""
    read -p "Press enter after you've copied the key to the server..."
    SSH_PRIVATE_KEY=$(cat ~/.ssh/github-deploy)
else
    echo "Available SSH keys:"
    ls -1 ~/.ssh/*.pub 2>/dev/null | sed 's/.pub$//'
    read -p "Enter path to private key: " KEY_PATH
    if [ ! -f "$KEY_PATH" ]; then
        echo -e "${RED}Error: Key file not found!${NC}"
        exit 1
    fi
    SSH_PRIVATE_KEY=$(cat "$KEY_PATH")
fi

# Set GitHub secrets
echo ""
echo -e "${GREEN}Step 4: Setting GitHub Secrets${NC}"
echo "Setting secrets in GitHub repository..."

gh secret set SSH_PRIVATE_KEY --body "$SSH_PRIVATE_KEY"
gh secret set SSH_HOST --body "$SSH_HOST"
gh secret set SSH_USER --body "$SSH_USER"
gh secret set SSH_PORT --body "$SSH_PORT"
gh secret set DEPLOY_PATH --body "$DEPLOY_PATH"
gh secret set SECRET_KEY --body "$SECRET_KEY"
gh secret set ADMIN_EMAIL --body "$ADMIN_EMAIL"
gh secret set ADMIN_PASSWORD --body "$ADMIN_PASSWORD"

echo ""
echo -e "${GREEN}✅ All secrets have been set successfully!${NC}"
echo ""
echo "GitHub Secrets configured:"
echo "  - SSH_PRIVATE_KEY"
echo "  - SSH_HOST: $SSH_HOST"
echo "  - SSH_USER: $SSH_USER"
echo "  - SSH_PORT: $SSH_PORT"
echo "  - DEPLOY_PATH: $DEPLOY_PATH"
echo "  - SECRET_KEY: <hidden>"
echo "  - ADMIN_EMAIL: $ADMIN_EMAIL"
echo "  - ADMIN_PASSWORD: <hidden>"
echo ""

# Create deployment summary
cat > .deployment-config << EOF
# Deployment Configuration
# Generated on $(date)

SSH_HOST=$SSH_HOST
SSH_USER=$SSH_USER
SSH_PORT=$SSH_PORT
DEPLOY_PATH=$DEPLOY_PATH
ADMIN_EMAIL=$ADMIN_EMAIL

# Next Steps:
# 1. Follow DEPLOYMENT.md to set up your server
# 2. Push to main branch to trigger deployment
# 3. Monitor deployment in GitHub Actions tab
EOF

echo -e "${GREEN}Configuration saved to .deployment-config${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Set up your server by following DEPLOYMENT.md"
echo "2. Push code to main branch: git push origin main"
echo "3. Monitor deployment in GitHub Actions"
echo ""
echo -e "${GREEN}Setup complete! 🚀${NC}"
