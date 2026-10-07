# 🛡️ SpikeShield

> **Event-Aware Internal Developer Platform (IDP), Predictive Flash-Crowd Auto-Scaler & Self-Healing SRE Autopilot for Amazon Elastic Beanstalk.**
>
> *Stop reacting to crashes. Start predicting them.*

[![AWS Elastic Beanstalk](https://img.shields.io/badge/AWS-Elastic_Beanstalk-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/elasticbeanstalk/)
[![AWS Region](https://img.shields.io/badge/Region-ap--south--1_(Mumbai)-232F3E?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18_+_TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Theme-Tailwind_Dark-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🇮🇳 The Problem: India's Flash-Crowd Traffic Stampedes

For any tech team building for hundreds of millions of digital users in India, traffic **never grows linearly or predictably**:
- **UPI Payment Webhooks**: 10,000+ TPS bursts during flash sales and bill-payment deadlines.
- **EdTech Result Portals**: NTA NEET UG & JEE result declarations spike traffic **50x–100x within 5 seconds**.
- **D2C & E-Commerce**: Diwali Big Billion countdowns crash checkout databases with cart stampedes.
- **IRCTC Tatkal Windows**: 10:00 AM AC & 11:00 AM Non-AC surges overwhelm connection pools.

### The Auto-Scaling Bottleneck
Traditional CloudWatch CPU-based auto-scaling takes **4 to 6 minutes** to notice a threshold breach, spawn an EC2 instance, install dependencies, and pass ALB health checks. By the time the new instance warms up, **Nginx has already crashed with 502/504 errors, connection pools are exhausted, and users are greeted with failure screens.**

**SpikeShield transforms Amazon Elastic Beanstalk into a predictive, self-healing SRE control plane that eliminates instance boot lag, hardens Nginx upstream pools, and saves heavily on cloud costs.**

---

## 🌐 Live AWS Production Infrastructure

SpikeShield is deployed live in **AWS `ap-south-1` (Mumbai)** across a dual-environment Blue/Green architecture:

| Environment | Role | Live URL | Status |
| :--- | :--- | :--- | :--- |
| **`spikeshield-prod`** | Primary Production | [http://spikeshield-prod.eba-ubvnfjix.ap-south-1.elasticbeanstalk.com](http://spikeshield-prod.eba-ubvnfjix.ap-south-1.elasticbeanstalk.com/) | 🟢 **Healthy / Ready** |
| **`spikeshield-staging`** | Zero-Downtime Rollback Target | [http://spikeshield-staging-510497.ap-south-1.elasticbeanstalk.com](http://spikeshield-staging-510497.ap-south-1.elasticbeanstalk.com/) | 🟢 **Healthy / Ready** |
| **Amazon SQS** | SRE Runbook Queue | `https://sqs.ap-south-1.amazonaws.com/510497448362/spikeshield-runbooks` | 🟢 **Operational** |
| **AWS CloudWatch** | Enhanced Health Telemetry | 60s Sliding Windows (5xx Rate, p99 Latency, RPS) | 🟢 **Active** |

---

## 🏗️ Architecture

```
                                  [ User Traffic / UPI Callbacks / Flash Crowds ]
                                                         │
                                                         ▼
                                       ┌───────────────────────────────────┐
                                       │   Application Load Balancer (ALB) │
                                       │        ap-south-1 (Mumbai)        │
                                       └─────────────────┬─────────────────┘
                                                         │
                                 ┌───────────────────────┴───────────────────────┐
                                 ▼                                               ▼
                    ┌─────────────────────────┐                     ┌─────────────────────────┐
                    │     spikeshield-prod    │                     │   spikeshield-staging   │
                    │  (Active Blue Env)      │  CNAME Rollback Swap│  (Green Target Env)     │
                    │                         │ ◄─────────────────► │                         │
                    │  • Nginx 65k nofile     │                     │  • Nginx 65k nofile     │
                    │  • Keepalive Pool (128) │                     │  • Keepalive Pool (128) │
                    │  • FastAPI Port 8000    │                     │  • FastAPI Port 8000    │
                    │  • Single-Page React UI │                     │  • Single-Page React UI │
                    └────────────┬────────────┘                     └─────────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Amazon EC2 ASG   │  │ Amazon SQS       │  │ AWS CloudWatch   │
│ Velocity Pre-Warm│  │ Runbook Queue    │  │ Enhanced Health  │
│ boto3 API        │  │ Async Remediation│  │ Telemetry Engine │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## ⚡ Key Capabilities

### 1. 🚀 Predictive Pre-Warming vs. Reactive CPU Scaling
Rather than waiting for CPU spikes, SpikeShield uses an **Event-Aware Velocity Engine**:
- Tracks `RequestCountPerTarget` slope acceleration in real time.
- Matches scheduled high-impact events (NEET results, IPL toss, Diwali sales) with IST time windows.
- Automatically adjusts AWS Auto Scaling Group desired capacity **20 minutes before flash crowds arrive**, eliminating instance boot delays entirely.

### 2. 🩺 Autonomous Self-Healing & Zero-Downtime Blue/Green Rollback
- Continuously monitors ALB 5xx error budgets and p99 target response latency.
- If a bad deploy breaches the error budget (>1.0% 5xx rate), the SRE engine automatically triggers an **Elastic Beanstalk CNAME Swap** (`swap_environment_cnames`) between production and staging.
- Degraded instances are safely drained and terminated while an automated **Root Cause Analysis (RCA)** card is dispatched to Slack.

### 3. 📦 Golden-Path `.platform` & `.ebextensions` Blueprints
Production-hardened, battle-tested Elastic Beanstalk configurations generated instantly with Jinja2:
- **UPI Webhook Profile**: Nginx `worker_rlimit_nofile 65535`, upstream keepalive pool of 128 connections, fast-fail proxy timeouts (10s), 200 r/s rate limits.
- **EdTech Result Portal Profile**: 30-second stale-while-revalidate micro-caching (`X-Cache-Status`) absorbing 100x exam result query stampedes at the reverse proxy layer.
- **D2C Flash-Sale Profile**: Segregated checkout rate limiting (10 r/s) vs catalog browsing (200 r/s) to prevent inventory racing.
- Instant 1-click **Download All as ZIP** bundle ready for `eb deploy`.

### 4. 🇮🇳 India-First FinOps Cost Engine
- Real-time instance inspection dynamically querying AWS for running EC2 types (`t3.micro`, Multi-AZ).
- Native **INR (₹) calculation** at ₹84.00/USD:
  - Real-time hourly cost (₹1.74/hr across 2 instances).
  - Daily run rate (₹41.76/day) & monthly projection.
  - **Unit Economics**: Measures cost in **₹ INR per 10,000 requests** to protect runway.
  - On-Demand vs. Spot blending optimizer projecting up to 58% cloud cost savings.

### 5. 💥 High-Speed Async Chaos Load Tester
- Built-in asynchronous HTTP load generator using `httpx.AsyncClient` with connection pooling.
- Generates real concurrent traffic bursts against target endpoints.
- Displays live sliding-window charts: Real-time RPS, p99 latency, and error rate percentages with interactive stop triggers.

### 6. 📨 Decoupled SRE Runbooks via Amazon SQS
- Web tier handles synchronous traffic while background remediation (rate-limit tuning, instance draining) is published to Amazon SQS.
- Backed by the `spikeshield-runbooks` queue in Mumbai.

---

## 🛠️ Tech Stack

- **Cloud Platform**: AWS Elastic Beanstalk (Python 3.11 on Amazon Linux 2023)
- **AWS Services**: EC2, Auto Scaling Groups, Application Load Balancers, CloudWatch, SQS, S3, IAM
- **Backend**: FastAPI 0.115, Uvicorn, boto3, Pydantic v2, Jinja2, Redis, httpx
- **Frontend**: React 18, TypeScript, TailwindCSS, Recharts, Lucide Icons, Vite
- **Reverse Proxy**: Nginx 1.24+ with custom `.platform/nginx/conf.d/` hooks
- **CI/CD**: GitHub Actions Blue/Green deployment workflow
- **AI Tooling**: Scaffolded and built with **Google Antigravity** (Advanced Agentic AI)

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- (Optional) Docker & Docker Compose

### 1. Clone & Configure
```bash
git clone https://github.com/your-username/spikeshield.git
cd spikeshield

# Configure backend environment
cp backend/.env.example backend/.env
```

### 2. Run Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start backend (defaults to MOCK_AWS=true for zero AWS charges)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Run Frontend (React / Vite)
```bash
cd ../frontend
npm install
npm run dev
```
- Dashboard: [http://localhost:5173](http://localhost:5173)

### 4. Or Run via Docker Compose
```bash
docker-compose up --build
```

---

## ☁️ Deploying to AWS Elastic Beanstalk

### Option A: 1-Click Automated Script
```bash
cd backend
python ../scratch/deploy_to_eb.py
```

### Option B: Via GitHub Actions CI/CD
1. Add the following repository secrets in GitHub (`Settings -> Secrets and variables -> Actions`):
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`: `ap-south-1`
   - `EB_APPLICATION_NAME`: `spikeshield-app`
   - `EB_ENVIRONMENT_NAME`: `spikeshield-prod`
   - `EB_STAGING_ENV_NAME`: `spikeshield-staging`
   - `EB_S3_BUCKET`: `elasticbeanstalk-ap-south-1-YOUR_ACCOUNT_ID`
2. Push any commit to `main`:
   ```bash
   git push origin main
   ```
   GitHub Actions will automatically package the bundle, upload to S3, deploy to Staging, run smoke tests, and execute a zero-downtime Blue/Green CNAME swap!

---

## ⚙️ Configuration Reference (`backend/.env`)

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `AWS_REGION` | `ap-south-1` | AWS region (Mumbai) |
| `AWS_ACCESS_KEY_ID` | `""` | IAM User Access Key |
| `AWS_SECRET_ACCESS_KEY` | `""` | IAM User Secret Key |
| `EB_APPLICATION_NAME` | `spikeshield-app` | Elastic Beanstalk Application name |
| `EB_ENVIRONMENT_NAME` | `spikeshield-prod` | Target Production Environment |
| `SQS_RUNBOOK_QUEUE_URL` | `""` | Amazon SQS Queue URL for SRE Runbooks |
| `SLACK_WEBHOOK_URL` | `""` | Incoming Slack Webhook for RCA & incident alerts |
| `MOCK_AWS` | `false` | Set `true` to run locally without AWS credentials |
| `VELOCITY_WINDOW_SECONDS`| `60` | Request rate calculation sliding window |
| `VELOCITY_SPIKE_THRESHOLD`| `2.5` | Slope multiplier triggering pre-warm |
| `ERROR_BUDGET_THRESHOLD_PCT`| `1.0` | 5xx error percentage triggering rollback |

---

## 📚 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Root health check for ALB & Nginx |
| `GET` | `/ws/telemetry` | WebSocket streaming live cluster metrics |
| `GET` | `/api/v1/environments` | Lists all Elastic Beanstalk environments & health |
| `GET` | `/api/v1/environments/{name}/instances` | Instance-level health, types, and AZs |
| `POST` | `/api/v1/scaling/prewarm` | Scales underlying AWS Auto Scaling Group capacity |
| `POST` | `/api/v1/blueprints/generate` | Generates `.platform` & `.ebextensions` bundles |
| `POST` | `/api/v1/chaos/spike` | Launches async HTTP load test |
| `GET` | `/api/v1/chaos/status/{job_id}` | Polls real-time RPS, latency, and error rates |
| `GET` | `/api/v1/finops/summary` | Cluster-wide ₹ INR costs & Spot projections |
| `POST` | `/api/v1/incidents/{id}/rollback` | Triggers zero-downtime Blue/Green CNAME swap |
| `POST` | `/api/v1/alerts/slack/configure` | Dynamically sets and verifies Slack webhook |

---

## 🤝 Acknowledgments & Credits

- Special thanks to **Shubham Londhe** and the **TrainWithShubham** community for championing real-world DevOps, cloud architecture, and platform engineering practices.
- Built and accelerated with **Google Antigravity** (Advanced Agentic AI Assistant).

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
