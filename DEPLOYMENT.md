# SAKEC Technology Business Incubator (TBI) Management Platform
## Production College Server Deployment & Administration Guide
### Developed by Dr. Rohan Appasaheb Borgalli
*Faculty Incharge, Technology Business Incubator (TBI)*  
*Shah & Anchor Kutchhi Engineering College (SAKEC), Chembur, Mumbai*  
*Contact: incubation@sakec.ac.in | +91 9821057992*

---

## 1. Executive Summary & Platform Architecture

The **SAKEC TBI Incubation Platform** is a custom, end-to-end digital ecosystem developed to monitor, simulate, and accelerate incubated startup companies at **Shah & Anchor Kutchhi Engineering College**. Aligned with the **CybraneX USim + WorkOS Incubation Platform** specifications, it integrates:

1. **WorkOS Business Digital Twin**: 360-degree operational workspace for founders to manage business models, team rosters, product roadmaps, sales pipelines, risk registers, and statutory milestones.
2. **USim Decision Simulator**: Algorithmic decision engine for unit economics, pricing elasticity, CAC/LTV estimation, burn rate projections, and 12-month runway forecasting.
3. **Unified Authority Dashboard**: Single-pane-of-glass executive overview for the Faculty Incharge, Principal, Dean R&D, and Management to monitor cohort health, milestone verifications, portfolio revenues, and NAAC/NIRF/NBA compliance metrics.
4. **Mentorship Review Hub**: Structured qualitative logs, milestone verification workflows, and 5-star health rating audits by internal and CybraneX industry mentors.
5. **Infinite Scaling Engine**: Initialized with **5 active startups** across SAKEC departments (EXTC, IT, Computer Engg, Cyber Security, AIDS, ECS) with built-in capability to scale to unlimited ventures.

---

## 2. Server Prerequisites

The application is engineered with **Python 3 standard library** and **SQLite3**, requiring **zero third-party pip dependencies** out-of-the-box.

- **Operating System:** Ubuntu 22.04 / 24.04 LTS, Debian 12, or RHEL 9 (College Data Center / Intranet Server)
- **Runtime:** Python 3.8+ (pre-installed on standard Linux distributions)
- **Web Server / Reverse Proxy:** Nginx 1.18+
- **Hardware:** 1 vCPU, 1 GB RAM, 10 GB Disk (Scalable to 1,000+ startups)
- **Network:** Port 80 / 443 (External/Campus Intranet), Port 8080 (Internal App Daemon)

---

## 3. Deployment Option A: Native Linux Service (Recommended)

### Step 1: Clone or Copy the Repository
```bash
sudo mkdir -p /var/www/sakec-tbi
sudo mkdir -p /var/lib/sakec_tbi
sudo cp -r /path/to/sakec_tbi_platform/* /var/www/sakec-tbi/
```

### Step 2: Initialize Database with Seed Data
```bash
sudo SAKEC_DB_PATH=/var/lib/sakec_tbi/sakec_tbi.db python3 /var/www/sakec-tbi/database.py
```

### Step 3: Configure File Ownership and Permissions
```bash
sudo chown -R www-data:www-data /var/www/sakec-tbi
sudo chown -R www-data:www-data /var/lib/sakec_tbi
sudo chmod -R 775 /var/lib/sakec_tbi
```

### Step 4: Install and Start Systemd Daemon
```bash
sudo cp /var/www/sakec-tbi/deploy/sakec-tbi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sakec-tbi.service
sudo systemctl start sakec-tbi.service
sudo systemctl status sakec-tbi.service
```

### Step 5: Configure Nginx Reverse Proxy
Copy the provided Nginx configuration:
```bash
sudo cp /var/www/sakec-tbi/deploy/nginx.conf /etc/nginx/sites-available/sakec-tbi
sudo ln -s /etc/nginx/sites-available/sakec-tbi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Enable HTTPS / SSL (Optional but Recommended)
```bash
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tbi.sakec.ac.in
```

---

## 4. Deployment Option B: Docker / Containerized Deployment

If your server runs Docker and Docker Compose:

```bash
cd /var/www/sakec-tbi/deploy
docker compose up -d --build
```
Verify container health:
```bash
docker ps
curl -s http://127.0.0.1:8080/api/analytics/portfolio
```

---

## 5. Pre-Configured User Accounts & Access Matrix

| Role | Username | Password | Full Name & Designation | Access Scope |
|---|---|---|---|---|
| **Faculty Incharge (Admin)** | `rohan.borgalli` | `Sakec@123` | **Dr. Rohan Appasaheb Borgalli** | Full Administrative Access, Milestone Verification, Scale-Up / Onboarding, System Diagnostics |
| **College Authority** | `principal` | `Sakec@123` | **Dr. Bhavesh Patel** (Principal) | Executive Portfolio View, Governance & Accreditation Dashboards, CSV Export |
| **Dean R&D** | `dean.rd` | `Sakec@123` | **Dean Research & Development** | Portfolio Analytics, Milestone Oversight |
| **Technical Mentor** | `mentor.tech` | `Sakec@123` | **Prof. Milind Khairnar** | Technical Mentorship Review, Milestone Audit |
| **Business Mentor** | `mentor.biz` | `Sakec@123` | **Ashwin S.** (CybraneX) | Business Model & USim Review |
| **Startup 1 Founder** | `founder.curadental` | `Sakec@123` | **Tanvi Sawant** (CuraDental AI) | CuraDental AI Digital Twin, Milestones, USim |
| **Startup 2 Founder** | `founder.edgefarm` | `Sakec@123` | **Aarav Mehta** (EdgeFarm IoT) | EdgeFarm IoT Workspace |
| **Startup 3 Founder** | `founder.edupulse` | `Sakec@123` | **Neha Kulkarni** (EduPulse) | EduPulse Analytics Workspace |
| **Startup 4 Founder** | `founder.cyberkavach` | `Sakec@123` | **Rishabh Shah** (CyberKavach) | CyberKavach Solutions Workspace |
| **Startup 5 Founder** | `founder.solargrid` | `Sakec@123` | **Kunal Jadhav** (SolarGridIQ) | SolarGridIQ Workspace |

*Note: Passwords can be modified directly by the user or updated by the administrator in the SQLite database.*

---

## 6. SAKEC Incubated Startups Overview

1. **CuraDental AI (Phase 4: Mentorship & Monitoring | Health: 93/100)**
   - *Domain:* HealthTech / Deep Learning Medical Image Analysis
   - *Department:* Electronics & Telecommunication (EXTC) & IT
   - *Traction:* 18 Active dental clinics and radiology hubs; ₹1,20,000 monthly revenue.

2. **EdgeFarm IoT (Phase 3: WorkOS Deployment | Health: 85/100)**
   - *Domain:* AgriTech / IoT Edge Computing
   - *Department:* Electronics & Computer Science (ECS)
   - *Traction:* 8 Commercial polyhouses in Maharashtra; ₹45,000 monthly revenue.

3. **EduPulse Analytics (Phase 4: Mentorship & Monitoring | Health: 89/100)**
   - *Domain:* EdTech / Outcome-Based Education (OBE) SaaS
   - *Department:* Computer Engineering
   - *Traction:* 12 Academic departments onboarded; ₹95,000 monthly revenue.

4. **CyberKavach Solutions (Phase 2: Business Simulation | Health: 79/100)**
   - *Domain:* Cyber Security / DPDP Act Compliance
   - *Department:* Cyber Security
   - *Traction:* 5 Active MSME beta pilots; ₹15,000 monthly revenue.

5. **SolarGridIQ (Phase 1: Digital Onboarding | Health: 76/100)**
   - *Domain:* CleanTech / Smart Microgrid AI
   - *Department:* AI & Data Science (AIDS) & EXTC
   - *Traction:* Campus pilot setup at SAKEC main building; prototype telemetry live.

---

## 7. Scaling to N Startups

To onboard a 6th, 7th, or 50th startup:
1. Log in as **Dr. Rohan Appasaheb Borgalli** (`rohan.borgalli`).
2. Navigate to the **"🚀 Incubator Admin & Scale-up"** tab.
3. Complete the onboarding form with Startup Name, Tagline, Department, Founder Details, and Initial Phase.
4. Click **"Complete Onboarding & Provision WorkOS Digital Twin"**.
5. The system automatically:
   - Registers the venture in the SQLite relational database.
   - Provisions a structured **WorkOS Business Digital Twin**.
   - Generates the standard **Phase 1 to Phase 5 Milestones roadmap**.
   - Initializes baseline financial health metrics.

---

## 8. Backup & Maintenance

Add a daily cron job to run the backup script:
```bash
sudo crontab -e
```
Append the following line to back up daily at 2:00 AM:
```cron
0 2 * * * /var/www/sakec-tbi/deploy/backup.sh > /var/log/sakec_tbi_backup.log 2>&1
```

---
*SAKEC Technology Business Incubator — Elevating Startups into Industry Leaders.*  
*Shah & Anchor Kutchhi Engineering College, Chembur, Mumbai.*
