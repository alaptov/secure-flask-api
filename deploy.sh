#!/bin/bash
# Deployment script for Secure Flask API
# Server: 172.237.101.94
# User: root
# Deployment Directory: /var/www/staff

set -e  # Exit on error

# Configuration
SERVER_IP="172.237.101.94"
SERVER_USER="root"
SERVER_PORT="22"
DEPLOY_DIR="/var/www/staff"
APP_NAME="secure-flask-api"
DOMAIN_OR_IP="172.237.101.94"  # Change to your domain if you have one

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Secure Flask API Deployment Script                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Test SSH connection
echo -e "${BLUE}[1/10]${NC} Testing SSH connection..."
if ssh -o ConnectTimeout=10 ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} "exit" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH connection successful${NC}"
else
    echo -e "${RED}✗ SSH connection failed${NC}"
    echo ""
    echo "Please ensure:"
    echo "1. Your SSH key is added to the server's authorized_keys"
    echo "2. Run this command to copy your SSH key:"
    echo "   ssh-copy-id -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP}"
    echo ""
    echo "Your SSH public key:"
    cat ~/.ssh/id_ed25519.pub 2>/dev/null || cat ~/.ssh/id_rsa.pub 2>/dev/null
    exit 1
fi

# Step 2: Install system packages
echo -e "${BLUE}[2/10]${NC} Installing system packages..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << 'ENDSSH'
    # Update package lists
    apt-get update -y

    # Install required packages
    apt-get install -y python3 python3-pip python3-venv nginx git supervisor

    echo "System packages installed successfully"
ENDSSH
echo -e "${GREEN}✓ System packages installed${NC}"

# Step 3: Create deployment directory
echo -e "${BLUE}[3/10]${NC} Creating deployment directory..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << ENDSSH
    mkdir -p ${DEPLOY_DIR}
    cd ${DEPLOY_DIR}
    echo "Deployment directory created at ${DEPLOY_DIR}"
ENDSSH
echo -e "${GREEN}✓ Deployment directory created${NC}"

# Step 4: Copy application files
echo -e "${BLUE}[4/10]${NC} Copying application files..."
rsync -avz --exclude='.git' --exclude='venv' --exclude='instance' \
    --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' \
    -e "ssh -p ${SERVER_PORT}" \
    . ${SERVER_USER}@${SERVER_IP}:${DEPLOY_DIR}/${APP_NAME}/
echo -e "${GREEN}✓ Application files copied${NC}"

# Step 5: Set up Python virtual environment
echo -e "${BLUE}[5/10]${NC} Setting up Python virtual environment..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << ENDSSH
    cd ${DEPLOY_DIR}/${APP_NAME}
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn
    echo "Virtual environment set up successfully"
ENDSSH
echo -e "${GREEN}✓ Virtual environment configured${NC}"

# Step 6: Configure environment variables
echo -e "${BLUE}[6/10]${NC} Configuring environment variables..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << ENDSSH
    cd ${DEPLOY_DIR}/${APP_NAME}

    # Copy example env file
    cp .env.example .env

    # Generate secure secret key
    SECRET_KEY=\$(python3 -c 'import secrets; print(secrets.token_hex(32))')

    # Update .env file
    sed -i "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=\${SECRET_KEY}/" .env
    sed -i "s/FLASK_ENV=development/FLASK_ENV=production/" .env
    sed -i "s|DATABASE_URL=sqlite:///instance/app.db|DATABASE_URL=sqlite:///${DEPLOY_DIR}/${APP_NAME}/instance/app.db|" .env

    # Create instance directory
    mkdir -p instance

    echo ".env file configured"
ENDSSH
echo -e "${GREEN}✓ Environment variables configured${NC}"

# Step 7: Initialize database
echo -e "${BLUE}[7/10]${NC} Initializing database..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << ENDSSH
    cd ${DEPLOY_DIR}/${APP_NAME}
    source venv/bin/activate
    export FLASK_ENV=production
    python3 << 'PYTHON'
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print("Database initialized successfully")
PYTHON
ENDSSH
echo -e "${GREEN}✓ Database initialized${NC}"

# Step 8: Set up Supervisor (process manager)
echo -e "${BLUE}[8/10]${NC} Setting up Supervisor..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << ENDSSH
    cat > /etc/supervisor/conf.d/${APP_NAME}.conf << 'EOF'
[program:${APP_NAME}]
directory=${DEPLOY_DIR}/${APP_NAME}
command=${DEPLOY_DIR}/${APP_NAME}/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app("production")'
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/${APP_NAME}.err.log
stdout_logfile=/var/log/${APP_NAME}.out.log
environment=PATH="${DEPLOY_DIR}/${APP_NAME}/venv/bin"
EOF

    # Reload supervisor
    supervisorctl reread
    supervisorctl update
    supervisorctl restart ${APP_NAME}

    echo "Supervisor configured"
ENDSSH
echo -e "${GREEN}✓ Supervisor configured${NC}"

# Step 9: Configure Nginx
echo -e "${BLUE}[9/10]${NC} Configuring Nginx..."
ssh ${SERVER_USER}@${SERVER_IP} -p ${SERVER_PORT} << ENDSSH
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default

    # Create nginx config
    cat > /etc/nginx/sites-available/${APP_NAME} << 'EOF'
server {
    listen 80;
    server_name ${DOMAIN_OR_IP};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files (if needed)
    location /static/ {
        alias ${DEPLOY_DIR}/${APP_NAME}/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/

    # Test nginx configuration
    nginx -t

    # Restart nginx
    systemctl restart nginx
    systemctl enable nginx

    echo "Nginx configured and restarted"
ENDSSH
echo -e "${GREEN}✓ Nginx configured${NC}"

# Step 10: Verify deployment
echo -e "${BLUE}[10/10]${NC} Verifying deployment..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${DOMAIN_OR_IP}/)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Deployment successful!${NC}"
else
    echo -e "${RED}✗ Deployment verification failed (HTTP $HTTP_CODE)${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Complete!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Application URL: http://${DOMAIN_OR_IP}"
echo "API Documentation: http://${DOMAIN_OR_IP}/api/"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: changeme123"
echo ""
echo "IMPORTANT: Change the admin password immediately!"
echo ""
echo "Useful commands:"
echo "  View logs: ssh ${SERVER_USER}@${SERVER_IP} 'tail -f /var/log/${APP_NAME}.out.log'"
echo "  Restart app: ssh ${SERVER_USER}@${SERVER_IP} 'supervisorctl restart ${APP_NAME}'"
echo "  Check status: ssh ${SERVER_USER}@${SERVER_IP} 'supervisorctl status ${APP_NAME}'"
echo ""
