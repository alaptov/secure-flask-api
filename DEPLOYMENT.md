# Deployment Guide

Complete guide for deploying the Secure Flask API to a production server.

## Server Information

- **IP Address**: 172.237.101.94
- **User**: root
- **Port**: 22
- **Deployment Directory**: /var/www/staff

## Prerequisites

Before deploying, ensure you have:

1. **SSH Access**: Your SSH key must be added to the server
2. **Server Requirements**:
   - Ubuntu 20.04+ or Debian 10+
   - Root or sudo access
   - At least 1GB RAM
   - 10GB disk space

## Quick Deployment

### Step 1: Set Up SSH Access

First, copy your SSH public key to the server:

```bash
ssh-copy-id -p 22 root@172.237.101.94
```

If prompted, enter the root password.

**Your SSH Public Key**:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOKnD8+DSg6WV5v24+PwP/3ydjqr4nrhFEz5mzBIOF71 derekilchuk@gmail.com
```

Alternatively, manually add the key:
```bash
# On the server
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOKnD8+DSg6WV5v24+PwP/3ydjqr4nrhFEz5mzBIOF71 derekilchuk@gmail.com" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Step 2: Run Deployment Script

Once SSH access is configured, run the automated deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will automatically:
1. Test SSH connection
2. Install required system packages
3. Create deployment directory
4. Copy application files
5. Set up Python virtual environment
6. Configure environment variables
7. Initialize database
8. Set up Supervisor (process manager)
9. Configure Nginx (web server)
10. Verify deployment

## Manual Deployment

If you prefer to deploy manually, follow these steps:

### 1. Install System Packages

```bash
ssh root@172.237.101.94 << 'EOF'
apt-get update -y
apt-get install -y python3 python3-pip python3-venv nginx git supervisor
EOF
```

### 2. Create Deployment Directory

```bash
ssh root@172.237.101.94 'mkdir -p /var/www/staff'
```

### 3. Copy Application Files

```bash
rsync -avz --exclude='.git' --exclude='venv' --exclude='instance' \
    --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' \
    . root@172.237.101.94:/var/www/staff/secure-flask-api/
```

### 4. Set Up Virtual Environment

```bash
ssh root@172.237.101.94 << 'EOF'
cd /var/www/staff/secure-flask-api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
EOF
```

### 5. Configure Environment

```bash
ssh root@172.237.101.94 << 'EOF'
cd /var/www/staff/secure-flask-api
cp .env.example .env

# Generate secure secret key
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Update .env file
sed -i "s/SECRET_KEY=your-secret-key-here/SECRET_KEY=${SECRET_KEY}/" .env
sed -i "s/FLASK_ENV=development/FLASK_ENV=production/" .env
sed -i "s|DATABASE_URL=sqlite:///instance/app.db|DATABASE_URL=sqlite:////var/www/staff/secure-flask-api/instance/app.db|" .env

mkdir -p instance
EOF
```

### 6. Initialize Database

```bash
ssh root@172.237.101.94 << 'EOF'
cd /var/www/staff/secure-flask-api
source venv/bin/activate
export FLASK_ENV=production
python3 -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
EOF
```

### 7. Configure Supervisor

Create `/etc/supervisor/conf.d/secure-flask-api.conf` on the server:

```ini
[program:secure-flask-api]
directory=/var/www/staff/secure-flask-api
command=/var/www/staff/secure-flask-api/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app("production")'
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/secure-flask-api.err.log
stdout_logfile=/var/log/secure-flask-api.out.log
environment=PATH="/var/www/staff/secure-flask-api/venv/bin"
```

Then reload Supervisor:

```bash
ssh root@172.237.101.94 << 'EOF'
supervisorctl reread
supervisorctl update
supervisorctl start secure-flask-api
EOF
```

### 8. Configure Nginx

Create `/etc/nginx/sites-available/secure-flask-api` on the server:

```nginx
server {
    listen 80;
    server_name 172.237.101.94;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/staff/secure-flask-api/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and restart Nginx:

```bash
ssh root@172.237.101.94 << 'EOF'
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/secure-flask-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
systemctl enable nginx
EOF
```

## Verification

After deployment, verify the application is running:

```bash
curl http://172.237.101.94/
```

You should see the homepage HTML.

## Access the Application

- **Homepage**: http://172.237.101.94/
- **Login**: http://172.237.101.94/auth/login
- **Register**: http://172.237.101.94/auth/register
- **API Documentation**: http://172.237.101.94/api/

## Default Credentials

- **Username**: admin
- **Password**: changeme123

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

## Management Commands

### View Logs

```bash
# Application logs
ssh root@172.237.101.94 'tail -f /var/log/secure-flask-api.out.log'

# Error logs
ssh root@172.237.101.94 'tail -f /var/log/secure-flask-api.err.log'

# Nginx access logs
ssh root@172.237.101.94 'tail -f /var/log/nginx/access.log'

# Nginx error logs
ssh root@172.237.101.94 'tail -f /var/log/nginx/error.log'
```

### Control Application

```bash
# Restart application
ssh root@172.237.101.94 'supervisorctl restart secure-flask-api'

# Stop application
ssh root@172.237.101.94 'supervisorctl stop secure-flask-api'

# Start application
ssh root@172.237.101.94 'supervisorctl start secure-flask-api'

# Check status
ssh root@172.237.101.94 'supervisorctl status secure-flask-api'
```

### Update Application

To update the application after making changes:

```bash
# 1. Copy updated files
rsync -avz --exclude='.git' --exclude='venv' --exclude='instance' \
    --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' \
    . root@172.237.101.94:/var/www/staff/secure-flask-api/

# 2. Restart application
ssh root@172.237.101.94 'supervisorctl restart secure-flask-api'
```

## SSL/HTTPS Setup (Optional)

For production, it's highly recommended to use HTTPS. Install Let's Encrypt SSL certificate:

```bash
ssh root@172.237.101.94 << 'EOF'
# Install certbot
apt-get install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
certbot --nginx -d yourdomain.com

# Auto-renewal
certbot renew --dry-run
EOF
```

## Firewall Configuration

Configure UFW firewall for security:

```bash
ssh root@172.237.101.94 << 'EOF'
# Allow SSH
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS (if using SSL)
ufw allow 443/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
EOF
```

## Troubleshooting

### Application Not Starting

Check logs:
```bash
ssh root@172.237.101.94 'tail -50 /var/log/secure-flask-api.err.log'
```

### Nginx Errors

Test configuration:
```bash
ssh root@172.237.101.94 'nginx -t'
```

View error log:
```bash
ssh root@172.237.101.94 'tail -50 /var/log/nginx/error.log'
```

### Database Issues

Reinitialize database:
```bash
ssh root@172.237.101.94 << 'EOF'
cd /var/www/staff/secure-flask-api
source venv/bin/activate
rm -f instance/app.db
python3 -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
supervisorctl restart secure-flask-api
EOF
```

## Security Recommendations

1. **Change Admin Password**: Immediately after deployment
2. **Use HTTPS**: Install SSL certificate with Let's Encrypt
3. **Update Regularly**: Keep system and packages updated
4. **Backup Database**: Regular backups of `instance/app.db`
5. **Monitor Logs**: Check logs regularly for suspicious activity
6. **Firewall**: Use UFW to restrict access
7. **Fail2Ban**: Install fail2ban to prevent brute-force attacks

## Performance Tuning

For better performance:

1. **Increase Gunicorn Workers**: Edit supervisor config, change `-w 4` to `-w 8` (2x CPU cores)
2. **Use PostgreSQL**: For production, use PostgreSQL instead of SQLite
3. **Add Redis**: For session storage and caching
4. **Enable Gzip**: In Nginx configuration
5. **CDN**: Use a CDN for static assets

## Backup Strategy

Create regular backups:

```bash
# Backup database
ssh root@172.237.101.94 'cd /var/www/staff/secure-flask-api && tar -czf ~/backup-$(date +%Y%m%d).tar.gz instance/'

# Download backup
scp root@172.237.101.94:~/backup-*.tar.gz ./backups/
```

## Support

For issues or questions:
- Check logs first
- Review this documentation
- Check GitHub repository: https://github.com/alaptov/secure-flask-api

---

**Deployed with security and performance in mind!**
