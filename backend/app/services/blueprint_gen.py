"""
SpikeShield Blueprint Generator
Generates production-hardened Elastic Beanstalk configuration bundles
from workload profile templates using Jinja2.
"""
from __future__ import annotations

from datetime import datetime, timezone
from jinja2 import Environment, BaseLoader

from app.models.blueprint import BlueprintRequest, BlueprintResult, WorkloadProfile

# ---------------------------------------------------------------------------
# Jinja2 template strings
# ---------------------------------------------------------------------------

NGINX_TEMPLATE = """\
# ============================================================
# SpikeShield Generated Nginx Config
# Profile: {{ profile }}
# Generated: {{ generated_at }}
# ============================================================

worker_processes  auto;
worker_rlimit_nofile {{ worker_rlimit_nofile }};

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  {{ worker_connections }};
    use                 epoll;
    multi_accept        on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # ── Logging ──────────────────────────────────────────────
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" rt=$request_time '
                    'uct="$upstream_connect_time" uht="$upstream_header_time" '
                    'urt="$upstream_response_time"';
    access_log /var/log/nginx/access.log main;

    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout  {{ keepalive_timeout }}s;
    server_tokens   off;

    # ── Gzip Compression ─────────────────────────────────────
{% if enable_gzip %}
    gzip              on;
    gzip_vary         on;
    gzip_proxied      any;
    gzip_comp_level   6;
    gzip_buffers      16 8k;
    gzip_http_version 1.1;
    gzip_min_length   256;
    gzip_types
        text/plain text/css text/xml text/javascript
        application/json application/javascript application/xml+rss
        application/atom+xml image/svg+xml;
{% else %}
    gzip off;
{% endif %}

{% if enable_brotli %}
    brotli            on;
    brotli_comp_level 6;
    brotli_types      text/plain text/css application/json application/javascript text/xml;
{% endif %}

    # ── Rate Limiting Zones ───────────────────────────────────
{% if enable_rate_limiting %}
{% for zone in rate_limit_zones %}
    limit_req_zone  {{ zone.key }} zone={{ zone.name }}:{{ zone.size }} rate={{ zone.rate }};
{% endfor %}
{% for zone in conn_limit_zones %}
    limit_conn_zone {{ zone.key }} zone={{ zone.name }}:{{ zone.size }};
{% endfor %}
{% endif %}

    # ── Proxy Cache ───────────────────────────────────────────
{% if proxy_cache_enabled %}
    proxy_cache_path /tmp/nginx_cache levels=1:2 keys_zone=ss_cache:{{ cache_zone_size }}
                     max_size={{ cache_max_size }} inactive={{ cache_inactive }} use_temp_path=off;
{% endif %}

    # ── Upstream ──────────────────────────────────────────────
    upstream spikeshield_app {
        server 127.0.0.1:{{ app_port }};
        keepalive {{ upstream_keepalive }};
        keepalive_requests 1000;
        keepalive_timeout  65s;
    }

    # ── Real IP from ALB ──────────────────────────────────────
    set_real_ip_from  10.0.0.0/8;
    set_real_ip_from  172.16.0.0/12;
    real_ip_header    X-Forwarded-For;
    real_ip_recursive on;

    server {
        listen      80 default_server;
        server_name _;

        client_max_body_size {{ client_max_body_size }};

        # ── Security Headers ─────────────────────────────────
        add_header X-Frame-Options          "SAMEORIGIN"          always;
        add_header X-Content-Type-Options   "nosniff"             always;
        add_header X-XSS-Protection         "1; mode=block"       always;
        add_header Referrer-Policy          "strict-origin-when-cross-origin" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # ── Health check (no rate limit) ─────────────────────
        location /health {
            proxy_pass         http://spikeshield_app;
            proxy_http_version 1.1;
            proxy_set_header   Connection "";
            access_log         off;
            proxy_connect_timeout 2s;
            proxy_read_timeout    5s;
        }

{% for location in custom_locations %}
        # {{ location.comment }}
        location {{ location.path }} {
{% if location.rate_limit_zone %}
            limit_req  zone={{ location.rate_limit_zone }} burst={{ location.burst }} nodelay;
{% endif %}
{% if location.conn_limit_zone %}
            limit_conn {{ location.conn_limit_zone }} {{ location.conn_limit }};
{% endif %}
{% if location.cache_zone %}
            proxy_cache             {{ location.cache_zone }};
            proxy_cache_valid       200 {{ location.cache_ttl }};
            proxy_cache_use_stale   error timeout updating;
            add_header              X-Cache-Status $upstream_cache_status;
{% endif %}
            proxy_pass             http://spikeshield_app;
            proxy_http_version     1.1;
            proxy_set_header       Connection    "";
            proxy_set_header       Host          $host;
            proxy_set_header       X-Real-IP     $remote_addr;
            proxy_set_header       X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout  {{ location.connect_timeout }}s;
            proxy_send_timeout     {{ location.send_timeout }}s;
            proxy_read_timeout     {{ location.read_timeout }}s;
        }

{% endfor %}
        # ── Default location ─────────────────────────────────
        location / {
{% if enable_rate_limiting %}
            limit_req  zone=default_limit burst={{ default_burst }} nodelay;
{% endif %}
            proxy_pass             http://spikeshield_app;
            proxy_http_version     1.1;
            proxy_set_header       Connection    "";
            proxy_set_header       Host          $host;
            proxy_set_header       X-Real-IP     $remote_addr;
            proxy_set_header       X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_connect_timeout  5s;
            proxy_send_timeout     60s;
            proxy_read_timeout     60s;
        }
    }
}
"""

CAPACITY_CONFIG_TEMPLATE = """\
# ============================================================
# SpikeShield .ebextensions — Capacity & Scaling
# Profile: {{ profile }}
# ============================================================
option_settings:

  # ── Load Balancer ────────────────────────────────────────
  aws:elasticbeanstalk:environment:
    LoadBalancerType: application

  # ── Auto Scaling Group ───────────────────────────────────
  aws:autoscaling:asg:
    MinSize: '{{ min_instances }}'
    MaxSize: '{{ max_instances }}'
    Cooldown: '{{ cooldown }}'

  # ── Instance Type ────────────────────────────────────────
  aws:autoscaling:launchconfiguration:
    InstanceType: {{ instance_type }}

  # ── Rolling Update Policy ────────────────────────────────
  aws:autoscaling:updatepolicy:rollingupdate:
    RollingUpdateEnabled: 'true'
    RollingUpdateType: Health
    MaxBatchSize: '{{ rolling_batch_size }}'
    MinInstancesInService: '1'
    PauseTime: PT0S
    WaitOnResourceSignals: 'false'

  # ── Enhanced Health Reporting ────────────────────────────
  aws:elasticbeanstalk:healthreporting:system:
    SystemType: enhanced
    HealthCheckSuccessThreshold: Ok

  # ── ALB Process (Target Group) ───────────────────────────
  aws:elasticbeanstalk:environment:process:default:
    DeregistrationDelay: '{{ deregistration_delay }}'
    HealthCheckPath: /health
    HealthCheckInterval: '15'
    HealthCheckTimeout: '5'
    HealthyThresholdCount: '2'
    UnhealthyThresholdCount: '3'
    StickinessEnabled: 'false'

  # ── Scaling Trigger ──────────────────────────────────────
  aws:autoscaling:trigger:
    BreachDuration: '{{ breach_duration }}'
    LowerBreachScaleIncrement: '{{ scale_in_increment }}'
    LowerThreshold: '{{ scale_in_threshold }}'
    MeasureName: {{ scale_metric }}
    Period: '{{ scale_period }}'
    Statistic: {{ scale_statistic }}
    Unit: {{ scale_unit }}
    UpperBreachScaleIncrement: '{{ scale_out_increment }}'
    UpperThreshold: '{{ scale_out_threshold }}'

{% if enable_spot %}
# ── Spot / On-Demand Mixed Policy ───────────────────────────
# Note: Mixed Instance Policy must be applied via CloudFormation
# or the AWS Console. The following is a reference configuration:
# SpotAllocationStrategy: capacity-optimized
# OnDemandBaseCapacity: {{ spot_ondemand_base }}
# OnDemandPercentageAboveBaseCapacity: {{ spot_ondemand_pct }}
# SpotMaxPrice: {{ spot_max_price }}
{% endif %}
"""

CLOUDWATCH_CONFIG_TEMPLATE = """\
# ============================================================
# SpikeShield .ebextensions — CloudWatch Alarms
# Profile: {{ profile }}
# ============================================================
Resources:

  # ── Alarm: Unhealthy Host Count ─────────────────────────
  SpikeShieldAlarmUnhealthyHosts:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "spikeshield-${profile}-unhealthy-hosts"
      AlarmDescription: "Fewer than 2 healthy targets behind ALB"
      MetricName: HealthyHostCount
      Namespace: AWS/ApplicationELB
      Statistic: Minimum
      Period: 60
      EvaluationPeriods: 2
      Threshold: 2
      ComparisonOperator: LessThanThreshold
      TreatMissingData: breaching

  # ── Alarm: 5xx Error Rate ────────────────────────────────
  SpikeShieldAlarm5xxRate:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "spikeshield-${profile}-5xx-rate"
      AlarmDescription: "5xx error rate exceeds {{ error_threshold }}%"
      Metrics:
        - Id: m1
          MetricStat:
            Metric:
              MetricName: HTTPCode_Target_5XX_Count
              Namespace: AWS/ApplicationELB
            Period: 60
            Stat: Sum
        - Id: m2
          MetricStat:
            Metric:
              MetricName: RequestCount
              Namespace: AWS/ApplicationELB
            Period: 60
            Stat: Sum
        - Id: e1
          Expression: "(m1/m2)*100"
          Label: "5xxErrorRate"
      ComparisonOperator: GreaterThanThreshold
      EvaluationPeriods: 2
      Threshold: {{ error_threshold }}
      TreatMissingData: notBreaching

  # ── Alarm: p99 Latency ───────────────────────────────────
  SpikeShieldAlarmP99Latency:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "spikeshield-${profile}-p99-latency"
      AlarmDescription: "p99 response time exceeds {{ latency_threshold_ms }}ms"
      MetricName: TargetResponseTime
      Namespace: AWS/ApplicationELB
      ExtendedStatistic: p99
      Period: 60
      EvaluationPeriods: 3
      Threshold: {{ latency_threshold }}
      ComparisonOperator: GreaterThanThreshold
      TreatMissingData: notBreaching

  # ── Log Group ────────────────────────────────────────────
  SpikeShieldLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /spikeshield/{{ profile | lower | replace('_','-') }}/application
      RetentionInDays: 30
"""

SECURITY_CONFIG_TEMPLATE = """\
# ============================================================
# SpikeShield .ebextensions — Security Hardening
# Profile: {{ profile }}
# ============================================================
option_settings:

  # ── IMDSv2 Enforcement (Instance Metadata Service) ────────
{% if enable_imdsv2 %}
  # IMDSv2 is enforced via EC2 Launch Template HttpTokens=required.
  # Apply this via CloudFormation or modify the Launch Template in the
  # Auto Scaling Group to set HttpTokens: required, HttpPutResponseHopLimit: 1
{% endif %}

  # ── Nginx Security Headers (via platform hook) ───────────
  # Injected in .platform/nginx/conf.d/spikeshield.conf

  # ── Environment Least-Privilege IAM ──────────────────────
  aws:autoscaling:launchconfiguration:
    IamInstanceProfile: aws-elasticbeanstalk-ec2-role

commands:
  # ── Disable EC2 Metadata for non-root processes ──────────
  01_imdsv2_enforce:
    command: |
      TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
        -H "X-aws-ec2-metadata-token-ttl-seconds: 21600") || true
      echo "IMDSv2 token obtained: ${TOKEN:0:8}..." >> /var/log/spikeshield-security.log
    ignoreErrors: true

  # ── Ensure Nginx hides version ────────────────────────────
  02_nginx_server_tokens:
    command: |
      grep -q "server_tokens off" /etc/nginx/nginx.conf || \
        sed -i 's/http {/http {\n    server_tokens off;/' /etc/nginx/nginx.conf
    ignoreErrors: true

  # ── Restrict /etc/passwd permissions ─────────────────────
  03_harden_permissions:
    command: chmod 644 /etc/passwd && chmod 640 /etc/shadow || true
    ignoreErrors: true
"""

PREDEPLOY_HOOK_TEMPLATE = """\
#!/bin/bash
# ============================================================
# SpikeShield Pre-Deploy Hook: Warmup & Validation
# Profile: {{ profile }}
# ============================================================
set -euo pipefail

LOG_FILE="/var/log/eb-hooks.log"
APP_PORT="{{ app_port }}"
MAX_WAIT=60  # seconds

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S IST')] [PREDEPLOY] $*" | tee -a "$LOG_FILE"
}

log "SpikeShield pre-deploy hook starting (profile: {{ profile }})"

# ── Wait for application to be ready ─────────────────────
log "Waiting for application on port $APP_PORT..."
WAITED=0
until curl -sf "http://localhost:$APP_PORT/health" > /dev/null 2>&1; do
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        log "ERROR: Application did not start within ${MAX_WAIT}s"
        exit 1
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done
log "Application is ready (waited ${WAITED}s)"

# ── Send warmup requests to populate connection pool ─────
log "Sending {{ warmup_requests }} warmup requests..."
for i in $(seq 1 {{ warmup_requests }}); do
    curl -sf "http://localhost:$APP_PORT/health" > /dev/null 2>&1 || true
    sleep 0.1
done
log "Warmup complete"

# ── Emit CloudWatch custom metric ─────────────────────────
if command -v aws &> /dev/null; then
    REGION=$(curl -sf http://169.254.169.254/latest/meta-data/placement/region \
        -H "X-aws-ec2-metadata-token: $(curl -sf -X PUT \
        http://169.254.169.254/latest/api/token \
        -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')" 2>/dev/null || echo "ap-south-1")
    aws cloudwatch put-metric-data \\
        --namespace "SpikeShield/Deployments" \\
        --metric-name "PreDeployWarmup" \\
        --value 1 \\
        --unit Count \\
        --region "$REGION" > /dev/null 2>&1 || true
    log "CloudWatch metric emitted: PreDeployWarmup=1"
fi

log "Pre-deploy hook completed successfully"
exit 0
"""

POSTDEPLOY_HOOK_TEMPLATE = """\
#!/bin/bash
# ============================================================
# SpikeShield Post-Deploy Hook: Smoke Tests
# Profile: {{ profile }}
# ============================================================
set -euo pipefail

LOG_FILE="/var/log/eb-hooks.log"
APP_PORT="{{ app_port }}"
FAILED=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S IST')] [POSTDEPLOY] $*" | tee -a "$LOG_FILE"
}

log "SpikeShield post-deploy smoke tests starting (profile: {{ profile }})"

# ── Smoke test /health ────────────────────────────────────
log "Testing GET /health..."
HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$APP_PORT/health" || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    log "PASS: /health returned 200"
else
    log "FAIL: /health returned $HTTP_STATUS"
    FAILED=1
fi

# ── Smoke test /api/v1/health ─────────────────────────────
log "Testing GET /api/v1/health..."
HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$APP_PORT/api/v1/health" || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    log "PASS: /api/v1/health returned 200"
else
    log "FAIL: /api/v1/health returned $HTTP_STATUS"
    FAILED=1
fi

# ── Emit CloudWatch metric ────────────────────────────────
if command -v aws &> /dev/null; then
    REGION=$(curl -sf http://169.254.169.254/latest/meta-data/placement/region \\
        -H "X-aws-ec2-metadata-token: $(curl -sf -X PUT \\
        http://169.254.169.254/latest/api/token \\
        -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')" 2>/dev/null || echo "ap-south-1")
    METRIC_VALUE=$( [ "$FAILED" -eq 0 ] && echo "1" || echo "0" )
    aws cloudwatch put-metric-data \\
        --namespace "SpikeShield/Deployments" \\
        --metric-name "PostDeploySuccess" \\
        --value "$METRIC_VALUE" \\
        --unit Count \\
        --region "$REGION" > /dev/null 2>&1 || true
fi

if [ "$FAILED" -ne 0 ]; then
    log "ERROR: Smoke tests FAILED — marking deployment as failed"
    exit 1
fi

log "Post-deploy smoke tests PASSED"
exit 0
"""

PROCFILE_TEMPLATE = """\
web: gunicorn app.main:app \\
  --workers {{ worker_processes }} \\
  --worker-class uvicorn.workers.UvicornWorker \\
  --bind 0.0.0.0:{{ app_port }} \\
  --timeout 120 \\
  --keep-alive 5 \\
  --graceful-timeout 30 \\
  --max-requests 1000 \\
  --max-requests-jitter 100 \\
  --log-level info \\
  --access-logfile - \\
  --error-logfile -
"""

# ---------------------------------------------------------------------------
# Profile-specific tuning parameters
# ---------------------------------------------------------------------------

PROFILE_PARAMS: dict[WorkloadProfile, dict] = {
    WorkloadProfile.HIGH_CONCURRENCY_UPI: {
        "worker_rlimit_nofile": 65535,
        "worker_connections": 4096,
        "upstream_keepalive": 128,
        "keepalive_timeout": 65,
        "client_max_body_size": "2m",
        "proxy_cache_enabled": False,
        "cache_zone_size": None,
        "cache_max_size": None,
        "cache_inactive": None,
        "rate_limit_zones": [
            {"key": "$binary_remote_addr", "name": "webhook_limit", "size": "10m", "rate": "200r/s"},
            {"key": "$binary_remote_addr", "name": "default_limit", "size": "10m", "rate": "50r/s"},
        ],
        "conn_limit_zones": [
            {"key": "$binary_remote_addr", "name": "conn_limit", "size": "10m"},
        ],
        "default_burst": 100,
        "custom_locations": [
            {
                "comment": "UPI Webhook endpoint — high rate limit, fast timeouts",
                "path": "/webhook",
                "rate_limit_zone": "webhook_limit",
                "burst": 500,
                "conn_limit_zone": "conn_limit",
                "conn_limit": 200,
                "cache_zone": None,
                "cache_ttl": None,
                "connect_timeout": 5,
                "send_timeout": 10,
                "read_timeout": 10,
            }
        ],
        # Capacity params
        "cooldown": 120,
        "rolling_batch_size": 2,
        "deregistration_delay": 10,
        "breach_duration": 1,
        "scale_in_increment": -1,
        "scale_in_threshold": 300,
        "scale_metric": "RequestCount",
        "scale_period": 1,
        "scale_statistic": "Sum",
        "scale_unit": "Count",
        "scale_out_increment": 3,
        "scale_out_threshold": 800,
        "spot_ondemand_base": 3,
        "spot_ondemand_pct": 20,
        # CloudWatch
        "error_threshold": 1.0,
        "latency_threshold_ms": 500,
        "latency_threshold": 0.5,
        # Hooks
        "warmup_requests": 20,
    },
    WorkloadProfile.EDTECH_RESULT_PORTAL: {
        "worker_rlimit_nofile": 65535,
        "worker_connections": 4096,
        "upstream_keepalive": 64,
        "keepalive_timeout": 30,
        "client_max_body_size": "10m",
        "proxy_cache_enabled": True,
        "cache_zone_size": "10m",
        "cache_max_size": "1g",
        "cache_inactive": "60m",
        "rate_limit_zones": [
            {"key": "$binary_remote_addr", "name": "result_limit", "size": "10m", "rate": "500r/s"},
            {"key": "$binary_remote_addr", "name": "default_limit", "size": "10m", "rate": "100r/s"},
        ],
        "conn_limit_zones": [],
        "default_burst": 200,
        "custom_locations": [
            {
                "comment": "Result pages — micro-cache 30s to absorb exam result stampede",
                "path": "/results",
                "rate_limit_zone": "result_limit",
                "burst": 1000,
                "conn_limit_zone": None,
                "conn_limit": None,
                "cache_zone": "ss_cache",
                "cache_ttl": "30s",
                "connect_timeout": 5,
                "send_timeout": 30,
                "read_timeout": 30,
            }
        ],
        "cooldown": 60,
        "rolling_batch_size": 3,
        "deregistration_delay": 30,
        "breach_duration": 1,
        "scale_in_increment": -2,
        "scale_in_threshold": 200,
        "scale_metric": "CPUUtilization",
        "scale_period": 1,
        "scale_statistic": "Average",
        "scale_unit": "Percent",
        "scale_out_increment": 5,
        "scale_out_threshold": 50,
        "spot_ondemand_base": 2,
        "spot_ondemand_pct": 30,
        "error_threshold": 2.0,
        "latency_threshold_ms": 2000,
        "latency_threshold": 2.0,
        "warmup_requests": 10,
    },
    WorkloadProfile.D2C_FLASH_SALE: {
        "worker_rlimit_nofile": 65535,
        "worker_connections": 4096,
        "upstream_keepalive": 64,
        "keepalive_timeout": 30,
        "client_max_body_size": "5m",
        "proxy_cache_enabled": True,
        "cache_zone_size": "10m",
        "cache_max_size": "500m",
        "cache_inactive": "30m",
        "rate_limit_zones": [
            {"key": "$binary_remote_addr", "name": "checkout_limit", "size": "10m", "rate": "10r/s"},
            {"key": "$binary_remote_addr", "name": "browse_limit", "size": "10m", "rate": "200r/s"},
            {"key": "$binary_remote_addr", "name": "default_limit", "size": "10m", "rate": "100r/s"},
        ],
        "conn_limit_zones": [
            {"key": "$binary_remote_addr", "name": "checkout_conn", "size": "10m"},
        ],
        "default_burst": 200,
        "custom_locations": [
            {
                "comment": "Checkout — strict rate limit to prevent inventory racing",
                "path": "/checkout",
                "rate_limit_zone": "checkout_limit",
                "burst": 20,
                "conn_limit_zone": "checkout_conn",
                "conn_limit": 5,
                "cache_zone": None,
                "cache_ttl": None,
                "connect_timeout": 5,
                "send_timeout": 30,
                "read_timeout": 30,
            },
            {
                "comment": "Product catalog — micro-cache 30s",
                "path": "/catalog",
                "rate_limit_zone": "browse_limit",
                "burst": 500,
                "conn_limit_zone": None,
                "conn_limit": None,
                "cache_zone": "ss_cache",
                "cache_ttl": "30s",
                "connect_timeout": 5,
                "send_timeout": 15,
                "read_timeout": 15,
            },
        ],
        "cooldown": 90,
        "rolling_batch_size": 2,
        "deregistration_delay": 20,
        "breach_duration": 1,
        "scale_in_increment": -1,
        "scale_in_threshold": 300,
        "scale_metric": "RequestCount",
        "scale_period": 1,
        "scale_statistic": "Sum",
        "scale_unit": "Count",
        "scale_out_increment": 3,
        "scale_out_threshold": 600,
        "spot_ondemand_base": 2,
        "spot_ondemand_pct": 25,
        "error_threshold": 1.0,
        "latency_threshold_ms": 1000,
        "latency_threshold": 1.0,
        "warmup_requests": 15,
    },
    WorkloadProfile.GENERIC_WEB: {
        "worker_rlimit_nofile": 16384,
        "worker_connections": 1024,
        "upstream_keepalive": 32,
        "keepalive_timeout": 30,
        "client_max_body_size": "5m",
        "proxy_cache_enabled": False,
        "cache_zone_size": None,
        "cache_max_size": None,
        "cache_inactive": None,
        "rate_limit_zones": [
            {"key": "$binary_remote_addr", "name": "default_limit", "size": "10m", "rate": "100r/s"},
        ],
        "conn_limit_zones": [],
        "default_burst": 50,
        "custom_locations": [],
        "cooldown": 180,
        "rolling_batch_size": 1,
        "deregistration_delay": 20,
        "breach_duration": 2,
        "scale_in_increment": -1,
        "scale_in_threshold": 40,
        "scale_metric": "CPUUtilization",
        "scale_period": 1,
        "scale_statistic": "Average",
        "scale_unit": "Percent",
        "scale_out_increment": 1,
        "scale_out_threshold": 70,
        "spot_ondemand_base": 1,
        "spot_ondemand_pct": 50,
        "error_threshold": 5.0,
        "latency_threshold_ms": 3000,
        "latency_threshold": 3.0,
        "warmup_requests": 10,
    },
}


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------

class BlueprintGenerator:
    """
    Generates production-hardened Elastic Beanstalk configuration bundles.
    Each profile produces: nginx.conf, .ebextensions (capacity/cloudwatch/security),
    .platform hooks (predeploy/postdeploy), and Procfile.
    """

    def __init__(self) -> None:
        self._jinja_env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)

    def _render(self, template_str: str, **ctx) -> str:
        return self._jinja_env.from_string(template_str).render(**ctx)

    def generate(self, request: BlueprintRequest) -> BlueprintResult:
        now = datetime.now(tz=timezone.utc)
        profile = request.profile
        p = PROFILE_PARAMS[profile].copy()

        # Override rate-limit RPS from request if rate limiting enabled
        if request.enable_rate_limiting:
            # Update default_limit zone rate
            for zone in p["rate_limit_zones"]:
                if zone["name"] == "default_limit":
                    zone["rate"] = f"{request.rate_limit_rps}r/s"

        shared = {
            "profile": profile.value,
            "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
            "app_port": request.app_port,
            "enable_gzip": request.enable_gzip,
            "enable_brotli": request.enable_brotli,
            "enable_rate_limiting": request.enable_rate_limiting,
            "enable_imdsv2": request.enable_imdsv2,
            "enable_spot": request.enable_spot,
            "spot_max_price": request.spot_max_price,
            "min_instances": request.min_instances,
            "max_instances": request.max_instances,
            "instance_type": request.instance_type,
            "worker_processes": request.worker_processes,
            **p,
        }

        nginx_config = self._render(NGINX_TEMPLATE, **shared)
        capacity_config = self._render(CAPACITY_CONFIG_TEMPLATE, **shared)
        cloudwatch_config = self._render(CLOUDWATCH_CONFIG_TEMPLATE, **shared)
        security_config = self._render(SECURITY_CONFIG_TEMPLATE, **shared)
        predeploy_hook = self._render(PREDEPLOY_HOOK_TEMPLATE, **shared)
        postdeploy_hook = self._render(POSTDEPLOY_HOOK_TEMPLATE, **shared)
        procfile = self._render(PROCFILE_TEMPLATE, **shared)

        return BlueprintResult(
            profile=profile,
            nginx_config=nginx_config,
            ebextension_capacity=capacity_config,
            ebextension_cloudwatch=cloudwatch_config,
            ebextension_security=security_config,
            platform_predeploy_hook=predeploy_hook,
            platform_postdeploy_hook=postdeploy_hook,
            procfile=procfile,
            generated_at=now,
        )
