# Deployment Guide - SSH Server with CI/CD

This guide will help you deploy the Flask application to your SSH server with automated CI/CD using GitHub Actions.

## Prerequisites

- Ubuntu/Debian server with SSH access
- Python 3.8+ installed on server
- Sudo privileges on server
- GitHub repository

## Step 1: Server Setup

### 1.1 Connect to Your Server

```bash
ssh user@your-server.com
```

### 1.2 Install Required Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx

# Install Gunicorn
sudo apt install -y gunicorn
```

### 1.3 Create Deployment Directory

```bash
# Create directory for the application
sudo mkdir -p /var/www/flask-app
sudo chown $USER:www-data /var/www/flask-app
sudo chmod 775 /var/www/flask-app
```

### 1.4 Set Up Systemd Service

```bash
# Copy the service file to systemd directory
sudo cp flask-app.service /etc/systemd/system/

# Update the service file with your deployment path and user
sudo nano /etc/systemd/system/flask-app.service

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable flask-app
```

### 1.5 Configure Nginx

```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/flask-app

# Update with your domain name
sudo nano /etc/nginx/sites-available/flask-app

# Enable the site
sudo ln -s /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 1.6 Set Up SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Step 2: GitHub Secrets Configuration

### 2.1 Generate SSH Key Pair (On Your Local Machine)

```bash
# Generate new SSH key for deployment
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github-deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/github-deploy.pub user@your-server.com

# Display private key (copy this for GitHub)
cat ~/.ssh/github-deploy
```

### 2.2 Add Secrets to GitHub

Go to your GitHub repository: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add the following secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `SSH_PRIVATE_KEY` | Content of `~/.ssh/github-deploy` | Private SSH key for deployment |
| `SSH_HOST` | `your-server.com` | Your server hostname or IP |
| `SSH_USER` | `your-username` | SSH username |
| `SSH_PORT` | `22` | SSH port (default 22) |
| `DEPLOY_PATH` | `/var/www` | Deployment directory path |
| `SECRET_KEY` | Generate with Python | Flask secret key |
| `ADMIN_EMAIL` | `admin@yourdomain.com` | Admin user email |
| `ADMIN_PASSWORD` | `your-secure-password` | Admin user password |

### 2.3 Generate Flask Secret Key

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Copy the output and add it as `SECRET_KEY` in GitHub secrets.

## Step 3: Server Sudoers Configuration

The deployment script needs to restart the systemd service. Add this to sudoers:

```bash
sudo visudo
```

Add this line (replace `your-username` with your SSH user):

```
your-username ALL=(ALL) NOPASSWD: /bin/systemctl start flask-app, /bin/systemctl stop flask-app, /bin/systemctl restart flask-app, /bin/systemctl status flask-app
```

## Step 4: Test Deployment

### 4.1 Manual Deployment Test

Push to the main branch:

```bash
git add .
git commit -m "Add CI/CD deployment"
git push origin main
```

### 4.2 Monitor Deployment

- Go to GitHub repository → `Actions` tab
- Watch the deployment workflow run
- Check for any errors

### 4.3 Verify on Server

```bash
# Check if service is running
sudo systemctl status flask-app

# Check application logs
sudo journalctl -u flask-app -f

# Test the application
curl http://localhost:8000
curl https://your-domain.com
```

## Step 5: Deployment Workflow

Once configured, deployment is automatic:

1. Push code to `main` branch
2. GitHub Actions triggers
3. Tests run automatically
4. If tests pass, deploys to server
5. Server automatically restarts application
6. Verifies deployment success

## Troubleshooting

### Deployment Fails

```bash
# Check GitHub Actions logs
# View the error in the Actions tab

# SSH into server and check logs
ssh user@your-server.com
sudo journalctl -u flask-app -n 50
```

### Application Won't Start

```bash
# Check service status
sudo systemctl status flask-app

# Check detailed logs
sudo journalctl -u flask-app -xe

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Manually test the application
cd /var/www/flask-app
source venv/bin/activate
python run.py
```

### Nginx Issues

```bash
# Test nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

### Permission Issues

```bash
# Fix permissions
sudo chown -R www-data:www-data /var/www/flask-app
sudo chmod -R 755 /var/www/flask-app
sudo chmod 775 /var/www/flask-app/instance
```

## Security Best Practices

1. **Use strong passwords** for admin accounts
2. **Keep SSH keys secure** - never commit private keys
3. **Enable firewall** on server:
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **Regular updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
5. **Monitor logs** regularly
6. **Use SSL/TLS** for production
7. **Set up automated backups**

## Rollback Procedure

If deployment fails, rollback to previous version:

```bash
ssh user@your-server.com
cd /var/www

# List available backups
ls -lh backup-*.tar.gz

# Restore from backup
tar -xzf backup-YYYYMMDD-HHMMSS.tar.gz
sudo systemctl restart flask-app
```

## Manual Deployment (Without CI/CD)

If you need to deploy manually:

```bash
# On local machine
tar -czf deploy.tar.gz --exclude='.git' --exclude='venv' .
scp deploy.tar.gz user@your-server.com:/var/www/

# On server
ssh user@your-server.com
cd /var/www
tar -xzf deploy.tar.gz -C flask-app
cd flask-app
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart flask-app
```

## Monitoring and Maintenance

### View Logs

```bash
# Application logs
sudo journalctl -u flask-app -f

# Nginx access logs
sudo tail -f /var/log/nginx/flask-app-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/flask-app-error.log
```

### Database Backup

```bash
# Backup database
cd /var/www/flask-app
tar -czf db-backup-$(date +%Y%m%d).tar.gz instance/

# Download backup to local
scp user@your-server.com:/var/www/flask-app/db-backup-*.tar.gz .
```

## Support

For issues:
1. Check GitHub Actions logs
2. Check server logs: `sudo journalctl -u flask-app`
3. Verify secrets are correctly set in GitHub
4. Ensure server has internet access
5. Check firewall rules

---

**Deployment Status**: Ready for production use with proper configuration.
