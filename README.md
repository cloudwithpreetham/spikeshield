# Shield SpikeShield

## SpikeShield - Event-Aware IDP & Self-Healing SRE Autopilot for Amazon Elastic Beanstalk

**Tagline**: Stop reacting to crashes. Start predicting them.

SpikeShield transforms Amazon Elastic Beanstalk from a basic hosting target into a Self-Service Internal Developer Platform (IDP) and Autonomous SRE Control Plane built for India's flash-crowd traffic patterns.

### The Problem
During massive events like NEET results, IPL tosses, Diwali sales, or Tatkal bookings, platforms face 50x-100x traffic spikes. Manual scaling is often too slow and reactive, leading to dropped connections and lost revenue.

### Features
🚀 **Event-Aware Scaling**: Automatically pre-warms environments ahead of known flash crowds.
🛡️ **Blueprint Profiles**: Pre-tuned Nginx and ASG configurations for different workloads (UPI, EdTech, D2C).
🩺 **Self-Healing SRE**: Detects anomalies and automatically provisions fallback capacity or isolates issues.
📊 **Chaos Engineering**: Built-in endpoints to simulate traffic spikes and test system resilience.

### Architecture
```
[ User Traffic ] --> [ ALB ] --> [ Nginx Rate Limiter ] --> [ SpikeShield App / FastApi ]
       |                                   |
       v                                   v
[ AWS Auto Scaling ] <-- [ SRE Autopilot ] --> [ Redis ]
```

### Quick Start
1. Clone the repository
   `git clone https://github.com/your-org/spikeshield.git`
2. Set up environment variables
   `cp .env.example .env`
3. Configure settings
   `Set MOCK_AWS=true in .env to run locally`
4. Start services
   `docker-compose up -d`

### Environment Variables
| Variable | Description |
|----------|-------------|
| AWS_REGION | AWS Region |
| AWS_ACCESS_KEY_ID | AWS Access Key |
| AWS_SECRET_ACCESS_KEY | AWS Secret Key |
| EB_APPLICATION_NAME | Elastic Beanstalk App Name |
| EB_ENVIRONMENT_NAME | Elastic Beanstalk Environment Name |
| REDIS_URL | Redis Connection URL |
| MOCK_AWS | Set to true for local testing without AWS creds |

### API Documentation
Available at: `http://localhost:8000/docs`

### Blueprint Profiles
| Profile | Use Case | Features |
|---------|----------|----------|
| `high-concurrency-upi` | Payment Systems | High connection limits, strict timeout controls |
| `edtech-result-portal` | Exam Results | Micro-caching, high burst limits |
| `d2c-flash-sale` | E-commerce | Differentiated rate limits for checkout vs browsing |
| `generic` | Standard Web App | Balanced baseline settings |

### Preset Events
| Event | Spike Multiplier | Behavior |
|-------|-----------------|----------|
| NEET Results | 100x | Huge stampede on result query endpoints |
| IPL Toss | 50x | Short burst over 5-10 minutes |
| Diwali Sale | 30x | Sustained high traffic with peaks at midnight |
| Tatkal Booking | 80x | Massive surge precisely at 10:00 AM / 11:00 AM |

### EB Deployment
SpikeShield comes with a built-in `.github/workflows/deploy.yml` that performs a Blue/Green deployment using AWS Elastic Beanstalk CNAME swapping. Push to the `main` branch to trigger a safe deployment process.

### Built With
- **Backend:** Python, FastAPI, boto3
- **Frontend:** React, TypeScript, TailwindCSS
- **Infrastructure:** Docker, Nginx, AWS Elastic Beanstalk
- **AI Tooling:** Built with Google Antigravity
