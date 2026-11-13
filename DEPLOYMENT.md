# CampusConnect — Production Deployment and Publishing Guide

This guide provides the complete, step-by-step procedure to enable, deploy, and publish **CampusConnect: Academic Progress and Communication Portal** to a live, secure HTTPS environment with full MySQL database connectivity and Telegram Bot API webhook integration.

---

## 1. Required Accounts & Credentials

| Service | Purpose | Required Output |
|---|---|---|
| **GitHub** (github.com) | Source code repository and automated cloud deployment triggers | Git repository URL |
| **Telegram** (telegram.org) | Bot creation and real-time student notifications | Bot Token and Bot Username (via `@BotFather`) |
| **Cloud Hosting Platform** (Render.com, Railway.app, or Ubuntu VPS) | Hosts the Flask WSGI application | Live public HTTPS URL (e.g. `https://campusconnect.onrender.com`) |
| **Cloud MySQL Database** (Aiven.io, Railway, or VPS MySQL) | Persistent relational data storage | MySQL connection string (`mysql+pymysql://...`) |

---

## 2. Environment Variables Specification

The live production deployment requires the following environment variables configured on your host:

| Variable | Description | Example / Recommended Value |
|---|---|---|
| `SECRET_KEY` | Cryptographic secret for signing session cookies | Random 64-char string (e.g. `openssl rand -hex 32`) |
| `DATABASE_URL` | SQLAlchemy MySQL connection URI | `mysql+pymysql://user:pass@host:port/campusconnect?charset=utf8mb4` |
| `ADMIN_NAME` | Default system administrator name | `Isha Dagar` |
| `ADMIN_EMAIL` | Default administrator sign-in email | `ish.isha.dagar@gmail.com` |
| `ADMIN_PASSWORD` | Secure initial password for admin account | `StrongAdminPass2026!` |
| `ADMIN_DEPARTMENT` | Department for administrator account | `Computer Applications` |
| `TELEGRAM_BOT_TOKEN` | API token from BotFather | `9249214038:AAFKplDVInEY7TO7ucWNLSgnVCQBYwXLx30` |
| `TELEGRAM_BOT_USERNAME` | Username of your Telegram bot | `campusConnBot` |
| `TELEGRAM_WEBHOOK_SECRET` | Secret token to authenticate Telegram webhook payloads | Random alphanumeric string (e.g. `campusconnect_secret_token_2026`) |
| `FLASK_DEBUG` | Disables debug mode in production | `0` |
| `MAX_CONTENT_LENGTH` | File upload ceiling (12 MB) | `12582912` |

---

## 3. Step 1: Telegram Bot Setup (via BotFather)

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`.
3. Enter a display name: `CampusConnect Alerts`.
4. Enter a username ending in `bot`: `campusConnBot` (or your chosen unique username).
5. BotFather will provide an HTTP API token:
   ```text
   Use this token to access the HTTP API:
   9249214038:AAFKplDVInEY7TO7ucWNLSgnVCQBYwXLx30
   ```
6. Optionally set bot commands by sending `/setcommands` to BotFather:
   ```text
   start - Get started with CampusConnect bot
   link - Connect your student account using a verification code
   help - Show help and instructions
   ```

---

## 4. Step 2: Database Setup (MySQL)

### Option A: Cloud Managed MySQL (Aiven.io or Railway)
1. Sign up on **Aiven.io** or **Railway.app**.
2. Create a new **MySQL** service (MySQL version 8.0+).
3. Connect using MySQL Workbench, DBeaver, or command line:
   ```bash
   mysql -h <HOST> -P <PORT> -u <USER> -p<PASSWORD> defaultdb
   ```
4. Execute the schema from `mysql_setup.sql`.
5. Copy the resulting connection URI in PyMySQL format:
   ```text
   mysql+pymysql://<USER>:<PASSWORD>@<HOST>:<PORT>/campusconnect?charset=utf8mb4
   ```

### Option B: Local / Self-Hosted MySQL
Run the following in PowerShell / terminal:
```bash
mysql -u root -p < mysql_setup.sql
```

---

## 5. Step 3: Deploy to Render.com (Recommended Free/Low-Cost Cloud Host)

Render provides automatic HTTPS (critical for Telegram Bot webhooks) and native Python support.

### 1. Push code to GitHub
Run from your local project directory:
```powershell
cd c:\Users\dsdag\OneDrive\Desktop\CampusConnect\CampusConnect
git init
git add .
git commit -m "Deploy CampusConnect production release"
git branch -M main
git remote add origin https://github.com/<your-username>/CampusConnect.git
git push -u origin main
```

### 2. Create Web Service on Render
1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository `CampusConnect`.
4. Configure the settings:
   - **Name:** `campusconnect-portal`
   - **Region:** Singapore / Frankfurt / Oregon (nearest to users)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     gunicorn app:app
     ```
5. Add the Environment Variables under **Environment**:
   - `SECRET_KEY`: `<your-random-secret>`
   - `DATABASE_URL`: `<your-mysql-uri>`
   - `ADMIN_EMAIL`: `ish.isha.dagar@gmail.com`
   - `ADMIN_PASSWORD`: `12345678`
   - `ADMIN_NAME`: `Isha Dagar`
   - `ADMIN_DEPARTMENT`: `Computer Applications`
   - `TELEGRAM_BOT_TOKEN`: `9249214038:AAFKplDVInEY7TO7ucWNLSgnVCQBYwXLx30`
   - `TELEGRAM_BOT_USERNAME`: `campusConnBot`
   - `TELEGRAM_WEBHOOK_SECRET`: `campusconnect_secret_token_2026`
   - `FLASK_DEBUG`: `0`
6. Click **Deploy Web Service**.
7. Wait 2–3 minutes until the status shows **Live** at your generated URL:
   `https://campusconnect-portal.onrender.com`.

---

## 6. Step 4: Alternative Deployment on Ubuntu Linux VPS (AWS EC2 / DigitalOcean)

If deploying on a dedicated Ubuntu 22.04/24.04 server:

```bash
# 1. Update and install packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx mysql-server certbot python3-certbot-nginx git

# 2. Configure MySQL
sudo mysql
# Inside MySQL:
# CREATE DATABASE campusconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
# CREATE USER 'campus_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';
# GRANT ALL PRIVILEGES ON campusconnect.* TO 'campus_user'@'localhost';
# FLUSH PRIVILEGES;
# EXIT;

# 3. Clone and setup application
sudo mkdir -p /var/www/campusconnect
sudo chown $USER:$USER /var/www/campusconnect
git clone https://github.com/<your-username>/CampusConnect.git /var/www/campusconnect
cd /var/www/campusconnect
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Create production .env file
nano .env

# 5. Create Systemd Service for Gunicorn
sudo nano /etc/systemd/system/campusconnect.service
```

Paste into `/etc/systemd/system/campusconnect.service`:
```ini
[Unit]
Description=CampusConnect Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/campusconnect
Environment="PATH=/var/www/campusconnect/.venv/bin"
ExecStart=/var/www/campusconnect/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable campusconnect
sudo systemctl start campusconnect
```

Configure Nginx reverse proxy:
```bash
sudo nano /etc/nginx/sites-available/campusconnect
```

Paste into `/etc/nginx/sites-available/campusconnect`:
```nginx
server {
    server_name your-domain.com;

    client_max_body_size 12M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and acquire SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/campusconnect /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d your-domain.com
```

---

## 7. Step 5: Register the Telegram Webhook

Telegram requires an HTTPS endpoint to deliver incoming messages (`/start`, `/link <code>`).

Run this command in PowerShell or terminal, replacing with your live URL, bot token, and secret token:

```bash
curl -F "url=https://your-domain.com/telegram/webhook" \
     -F "secret_token=campusconnect_secret_token_2026" \
     https://api.telegram.org/bot9249214038:AAFKplDVInEY7TO7ucWNLSgnVCQBYwXLx30/setWebhook
```

### Expected Output:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Verify Webhook Health:
```bash
curl https://api.telegram.org/bot9249214038:AAFKplDVInEY7TO7ucWNLSgnVCQBYwXLx30/getWebhookInfo
```

---

## 8. Live Verification Checklist

Once deployed, follow this verification sequence:

1. **Administrator Access:**
   - Navigate to `https://your-domain.com/login`.
   - Sign in with `ish.isha.dagar@gmail.com` / `12345678`.
   - Verify the Administrator Dashboard loads with User, Course, Task, and Submission stat cards.
2. **Faculty Workflow:**
   - Sign in as `cosmena@vips.edu` / `FacultyPass123`.
   - Navigate to **Create Task** (`/tasks/new`).
   - Create a test assignment with title `Cloud Deployment Verification Test`.
   - Verify task appears in the dashboard and task filter list.
3. **Student Workflow:**
   - Open an incognito browser window and navigate to `/register`.
   - Create student account: `Student Tester`, `tester@vips.edu`, password `StudentPass123`.
   - Log in as administrator and enrol `Student Tester` into `MCA-101`.
   - Log back in as `Student Tester`, open the task, and upload a test PDF file (< 12 MB).
   - Verify status transitions to `Submitted`.
4. **Telegram Linking Verification:**
   - From the student account, navigate to `/telegram`.
   - Click **Generate Verification Code**.
   - Open `@campusConnBot` in Telegram, send `/start`, then `/link <generated-code>`.
   - Verify the bot replies with confirmation.
   - On the web portal, refresh `/telegram` and confirm status shows `Connected`.
   - Click **Send Test Notification** and verify receipt in Telegram.
5. **Zero Emojis Verification:**
   - Verify that all buttons, labels, and status badges display plain text and clean typography with no emojis.
