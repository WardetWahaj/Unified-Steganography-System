# Deployment Guide - Unified Steganography System

> Complete step-by-step guide for deploying to various platforms

---

## Table of Contents

1. [Platform Comparison](#platform-comparison)
2. [Recommended: Render.com](#1-recommended-rendercom)
3. [Alternative: Railway.sh](#2-alternative-railwaysh)
4. [Alternative: Fly.io](#3-alternative-flyio)
5. [Not Recommended: Vercel (Workaround)](#4-not-recommended-vercel-workaround)
6. [Custom VPS/Server Deployment](#5-custom-vpsserver-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Platform Comparison

| Feature | Render | Railway | Fly.io | Vercel | AWS EC2 |
|---------|--------|---------|--------|--------|---------|
| **Best For** | FastAPI | Full-stack | Docker | Frontend | Control |
| **Startup Time** | 30-60s | 30-60s | 60-120s | Instant | Instant |
| **Max Runtime** | Unlimited | Unlimited | Unlimited | 60-900s | Unlimited |
| **Storage** | Paid disk | Limited | Paid disk | Ephemeral | Paid |
| **Free Tier** | Yes | No | Limited | Yes | No |
| **Cold Start** | 15-30s | 15-30s | 30-60s | 1-2s | None |
| **Best for Heavy Processing** | ✅ Yes | ⚠️ Partial | ✅ Yes | ❌ No | ✅ Yes |
| **Easiest Setup** | ✅ Yes | ⚠️ Medium | ⚠️ Medium | ✅ Yes | ❌ Complex |
| **Cost (Entry)** | Free | $5/mo | Free | Free | $3.5/mo |

---

## 1. RECOMMENDED: Render.com

### Why Render?

✅ Perfect match for FastAPI  
✅ Free tier for development/testing  
✅ Long-running processes supported  
✅ Easy GitHub integration  
✅ SQLite or PostgreSQL support  
✅ No timeout on background jobs  

### Quick Deploy (5 minutes)

##### Step 1: Prepare Your Code

```bash
# Make sure everything is committed
git status
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

##### Step 2: Create Render Account

1. Go to https://dashboard.render.com/
2. Click "Sign up" or "Sign in with GitHub"
3. Authorize GitHub access

##### Step 3: Create Web Service

```
Dashboard → New + → Web Service → Select Repository
```

Choose your `SteganoGraphy` repository

##### Step 4: Configure Service

**Basic Settings:**

| Setting | Value |
|---------|-------|
| **Name** | `steganography` (your choice) |
| **Environment** | `Python 3` |
| **Region** | `Oregon` (closest to US) |
| **Plan** | `Free` (to test) |

**Build Configuration:**

| Field | Value |
|-------|-------|
| **Root Directory** | `.` (leave empty) |
| **Build Command** | `pip install -r backend/config/requirements.txt` |
| **Start Command** | `cd backend && gunicorn -w 2 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT --timeout 120` |

**Environment Variables:**

Click "Add Environment Variable" and add:

```
PYTHON_VERSION = 3.11
PYTHONUNBUFFERED = 1
RENDER = true
SECRET_KEY = your-secret-key-generate-one
```

To generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

##### Step 5: Deploy

1. Click "Create Web Service"
2. Wait for deployment (2-5 minutes)
3. Check logs for errors
4. Access your API:

```
https://steganography.onrender.com
```

### Testing Deployment

```bash
# Test health endpoint
curl https://steganography.onrender.com/health

# Test API docs
curl https://steganography.onrender.com/docs

# Test registration
curl -X POST https://steganography.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456",
    "email": "test@example.com",
    "fullname": "Test User"
  }'
```

### Render Production Setup

#### Upgrade Plan for Production

Recommended: **Starter Plan ($7/month)**

```
Settings → Plan → Change to Starter
```

Benefits:
- Always on (doesn't sleep)
- 512MB RAM (vs free 0.5GB that sleeps)
- 24/7 uptime

#### Add Persistent Disk

For storing user keys and uploads:

```
Environment → Add Disk
- Name: stego-data
- Mount Path: /var/data
- Size: 10GB (or more)
```

Update Start Command:

```bash
cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT --timeout 300
```

#### Add PostgreSQL (Optional)

Better than SQLite for production:

```
Dashboard → New + → PostgreSQL
- Plan: Standard ($15/month)
```

Get connection string:

```
DATABASE_URL = postgresql://user:pass@render-host/dbname
```

Update your app to use PostgreSQL:

```python
# backend/models.py
import os

DB_PATH = os.environ.get('DATABASE_URL', 'sqlite:///stego_system.db')
# Use SQLAlchemy or similar for PostgreSQL support
```

#### Enable Auto-Deploys

```
Settings → Source Control
- Auto-Deploy: Yes
- Deploy on push to: main
```

Now deployment happens automatically on each `git push`!

#### Set Up Monitoring

```
Metrics & Logs → View
- Monitor CPU, Memory, and HTTP status codes
- Set up alerts for errors
```

### Render Redeploy

If needed to redeploy manually:

```
Dashboard → Select Service → Manual Deploy → Deploy
```

Or via Git:

```bash
git commit --allow-empty -m "Trigger rebuild on Render"
git push origin main
```

---

## 2. ALTERNATIVE: Railway.sh

### Why Railway?

✅ Similar to Render  
✅ More customizable environment  
✅ Good documentation  
⚠️ No free tier (cheapest: $5/month, only for first $5 credit)  

### Deployment Steps

#### Step 1: Install Railway CLI

**Windows (PowerShell):**
```powershell
choco install railway
```

**Or using npm:**
```bash
npm install -g @railway/cli
```

**Linux/Mac:**
```bash
curl -fsSL https://raw.githubusercontent.com/railwayapp/cli/main/install.sh | bash
```

#### Step 2: Login to Railway

```bash
railway login
```

This opens browser for authentication

#### Step 3: Create New Project

```bash
cd SteganoGraphy
railway init
```

Follow prompts and select your GitHub repo

#### Step 4: Configure Environment

Set environment variables:

```bash
railway variables set PYTHON_VERSION=3.11
railway variables set PYTHONUNBUFFERED=1
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

#### Step 5: Create railway.toml

Create file: `railway.toml`

```toml
[build]
builder = "dockerfile"

[start]
cmd = "cd backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app --bind 0.0.0.0:$PORT"

[env]
PORT = "8000"
PYTHONUNBUFFERED = "1"
PYTHON_VERSION = "3.11"
```

#### Step 6: Deploy

```bash
railway up
```

#### Step 7: View Logs

```bash
railway logs -f
```

#### Step 8: Get Service URL

```bash
railway domain
```

Visit: `https://your-service.railway.app`

---

## 3. ALTERNATIVE: Fly.io

### Why Fly.io?

✅ Docker-based (more control)  
✅ Global edge network  
✅ Free tier available  
✅ Affordable ($0.15/unit/month)  

### Deployment Steps

#### Step 1: Install Fly CLI

**Windows (PowerShell):**
```powershell
choco install flyctl
```

**Linux/Mac:**
```bash
curl -L https://fly.io/install.sh | sh
```

#### Step 2: Authenticate

```bash
fly auth login
```

#### Step 3: Create Dockerfile

Create: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/config/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/stego_uploads /tmp/stego_outputs /tmp/stego_keys

# Expose port
EXPOSE 8080

# Run server
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "backend.api.app:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
```

#### Step 4: Create Fly Config

Run:
```bash
fly launch
```

Fill in prompts. Creates `fly.toml`

Edit `fly.toml`:

```toml
app = "steganography"
primary_region = "sjc"  # San Jose

[build]
dockerfile = "./Dockerfile"

[env]
PYTHONUNBUFFERED = "1"
SECRET_KEY = "your-secret-key"

[[services]]
ports = [{handlers = ["http"], port = 8080}]

[mounts]
source = "stego_data"
destination = "/var/data"
size_gb = 10
```

#### Step 5: Create Volume (for persistence)

```bash
fly volumes create stego_data -r sjc --size 10
```

#### Step 6: Deploy

```bash
fly deploy
```

#### Step 7: Monitor

```bash
fly status
fly logs
```

#### Step 8: Access

```bash
fly open
```

Open API docs at: `https://your-app-name.fly.dev/docs`

---

## 4. NOT RECOMMENDED: Vercel (Workaround)

### Why NOT Vercel?

❌ Serverless functions timeout: Max 60s (Free) or 900s (Pro)  
❌ No persistent storage between requests  
❌ 512MB memory limit  
❌ Poor for media processing  
❌ No background jobs  

**Your steganography operations regularly exceed these limits.**

### If You Really Want Vercel...

You can deploy only the **frontend** to Vercel and use a **separate API** (on Render/Railway):

#### Architecture

```
Vercel Frontend ← API Calls → Render Backend
   (Hosting)                   (Processing)
```

#### Step 1: Create Frontend Project

Create a Next.js project:

```bash
npx create-next-app@latest frontend
cd frontend
```

#### Step 2: Create Proxy API Routes

```javascript
// pages/api/stego/hide.js
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

export const config = {
  api: {
    bodyParser: {
      sizeLimit: '100mb',
    },
  },
};

export default async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const response = await fetch(
      `${BACKEND_URL}/api/operations/hide/image`,
      {
        method: 'POST',
        headers: {
          'Authorization': req.headers.authorization,
          ...req.headers,
        },
        body: req.body,
      }
    );

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
```

#### Step 3: Create vercel.json

```json
{
  "buildCommand": "npm run build",
  "serverlessFunctionRegion": "sjc1",
  "functions": {
    "pages/api/**": {
      "memory": 3008,
      "maxDuration": 60
    }
  },
  "env": {
    "NEXT_PUBLIC_BACKEND_URL": "@backend_url"
  }
}
```

#### Step 4: Configure Environment

Add to Vercel project settings:

```
Settings → Environment Variables

NEXT_PUBLIC_BACKEND_URL = https://your-api.onrender.com
```

#### Step 5: Deploy to Vercel

```bash
git add .
git commit -m "Deploy frontend to Vercel"
git push origin main
```

Connect to Vercel dashboard and select the `frontend` directory.

#### Result

✅ Fast frontend on Vercel  
✅ Powerful backend on Render  
✅ Works around Vercel limitations  
✅ Cost-effective  

**Downside**: Two separate deployments to manage

---

## 5. CUSTOM VPS/SERVER DEPLOYMENT

### Best for: Total Control

Suitable for: DigitalOcean, Linode, AWS EC2, Vultr

#### Step 1: Get Server

Choose your VPS provider:
- **DigitalOcean**: $5-6/month droplet
- **Linode**: $5-10/month
- **Vultr**: $2.50-5/month
- **AWS EC2**: t2.micro free tier

Get a server with:
- ✅ Ubuntu 22.04 LTS
- ✅ 2GB+ RAM
- ✅ 20GB+ storage

#### Step 2: Connect to Server

```bash
ssh root@your-server-ip
```

#### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python and pip
apt install python3.11 python3-pip python3-venv -y

# Install system packages
apt install git ffmpeg libsm6 libxext6 -y

# Install Nginx (reverse proxy)
apt install nginx -y

# Install SSL (Let's Encrypt)
apt install certbot python3-certbot-nginx -y
```

#### Step 4: Clone Project

```bash
cd /home
git clone https://github.com/your-username/SteganoGraphy.git
cd SteganoGraphy

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/config/requirements.txt
```

#### Step 5: Create Systemd Service

Create: `/etc/systemd/system/steganography.service`

```ini
[Unit]
Description=Unified Steganography System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/SteganoGraphy
Environment="PATH=/home/SteganoGraphy/venv/bin"
ExecStart=/home/SteganoGraphy/venv/bin/gunicorn \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 127.0.0.1:8000 \
  --timeout 120 \
  backend.api.app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 6: Start Service

```bash
systemctl daemon-reload
systemctl enable steganography
systemctl start steganography
systemctl status steganography
```

#### Step 7: Configure Nginx

Create: `/etc/nginx/sites-available/steganography`

```nginx
upstream steganography {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://steganography;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /static {
        alias /home/SteganoGraphy/backend/static;
        expires 30d;
    }
}
```

#### Step 8: Enable SSL

```bash
certbot --nginx -d your-domain.com
```

#### Step 9: Start Nginx

```bash
systemctl restart nginx
systemctl enable nginx
```

#### Step 10: Access

```
https://your-domain.com
https://your-domain.com/docs
```

---

## Troubleshooting

### Problem: "Build failed on Render"

**Solution:**

```bash
# Check requirements.txt exists
ls backend/config/requirements.txt

# Verify Python version compatibility
python3 --version

# Test build locally
pip install -r backend/config/requirements.txt

# Push all changes
git add .
git commit -m "Fix build"
git push
```

### Problem: "Port already in use"

**Solution:**

```bash
# Find process using port
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port in config
```

### Problem: "Database locked" (SQLite on shared filesystem)

**Solution:**

Use PostgreSQL instead of SQLite for deployed systems:

```bash
# On Render, add PostgreSQL instance
# Update requirements to include psycopg2-binary
# Use DATABASE_URL environment variable
```

### Problem: "Memory exceeded"

**Solution:**

```bash
# Reduce workers
gunicorn -w 1 ...  # instead of -w 4

# Upgrade plan
# Or use PostgreSQL to reduce local RAM usage
```

### Problem: "Timeouts on large files"

**Solution:**

Increase timeout in start command:

```bash
--timeout 300  # 5 minutes
# or
--timeout 600  # 10 minutes
```

For very large files, implement streaming:

```python
# backend/crypto/streaming_crypto.py
# Already implemented in your project!
```

### Problem: "GPU not available"

**Solution - Not needed on cloud:**

```python
# GPU is optional
# Set in environment or code
USE_GPU = False

# Your app gracefully falls back to CPU
```

### Problem: "Logs not showing"

**Solution:**

```bash
# Render: Settings → Logs
# Railway: railway logs -f
# Fly.io: fly logs

# Or SSH and check directly
journalctl -u steganography -f
```

---

## Final Comparison & Recommendation

### For Development/Testing
👉 **Use Render Free Tier**
- Free tier available
- Good for testing
- Easy setup
- Auto-deploys on git push

### For Production
👉 **Use Render Starter Plan ($7/month)**
- Reliable uptime
- 24/7 monitoring
- Easy scaling
- Persistent disk storage

### For Maximum Control
👉 **Use VPS (DigitalOcean $5/month)**
- Full control
- No cold starts
- Can optimize everything
- More work to maintain

### For Global Distribution
👉 **Use Fly.io**
- Edge deployment
- Low latency worldwide
- Good documentation
- Free tier available

---

## Quick Commands Reference

### Render
```bash
# View logs
# Settings → View Logs

# Redeploy
# Select service → Manual Deploy

# Auto-deploy on push
git push origin main
```

### Railway
```bash
railway logs -f
railway variables
railway domain
railway up
```

### Fly.io
```bash
fly logs
fly status
fly open
fly deploy
```

### VPS
```bash
systemctl status steganography
journalctl -u steganography -f
```

---

**Happy Deploying! 🚀**
