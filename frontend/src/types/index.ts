export type HealthColor = 'Green' | 'Yellow' | 'Red' | 'Grey';
export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type WorkloadProfile = 'HIGH_CONCURRENCY_UPI' | 'EDTECH_RESULT_PORTAL' | 'D2C_FLASH_SALE' | 'GENERIC_WEB';
export type EventType = 'EXAM_RESULT' | 'FLASH_SALE' | 'SPORTS_EVENT' | 'BOOKING_WINDOW' | 'CUSTOM';

export interface EnvironmentHealth {
  env_name: string;
  env_id: string;
  status: string;
  health: HealthColor;
  health_status: string;
  instances_info: Record<string, number>;
  causes: string[];
  refreshed_at: string;
}

export interface EnvironmentDetail extends EnvironmentHealth {
  platform_arn: string;
  solution_stack: string;
  cname: string;
  endpoint_url: string;
  created_at: string;
  updated_at: string;
  tier: string;
}

export interface MetricsSnapshot {
  env_name: string;
  timestamp: string;
  rps: number;
  p99_latency_ms: number;
  cpu_percent: number;
  five_xx_rate: number;
  healthy_hosts: number;
}

export interface IncidentEvent {
  incident_id: string;
  env_name: string;
  severity: Severity;
  type: string;
  description: string;
  detected_at: string;
  resolved_at: string | null;
  actions_taken: string[];
}

export interface ScheduledEvent {
  event_id: string;
  name: string;
  type: EventType;
  scheduled_at: string;
  expected_peak_rps: number;
  env_name: string;
  description: string;
  created_at: string;
  is_active: boolean;
}

export interface BlueprintRequest {
  profile: WorkloadProfile;
  app_port: number;
  worker_processes: number;
  max_connections: number;
  enable_rate_limiting: boolean;
  rate_limit_rps: number;
  enable_gzip: boolean;
  enable_brotli: boolean;
  enable_imdsv2: boolean;
  instance_type: string;
  min_instances: number;
  max_instances: number;
  enable_spot: boolean;
  spot_max_price: string;
  custom_env_vars: Record<string, string>;
}

export interface BlueprintResult {
  profile: WorkloadProfile;
  nginx_config: string;
  ebextension_capacity: string;
  ebextension_cloudwatch: string;
  ebextension_security: string;
  platform_predeploy_hook: string;
  platform_postdeploy_hook: string;
  procfile: string;
  generated_at: string;
}

export interface EnvironmentCost {
  env_name: string;
  instances: Array<{
    instance_type: string;
    count: number;
    hourly_rate_usd: number;
    is_spot: boolean;
    hourly_cost_inr: number;
  }>;
  total_hourly_inr: number;
  total_daily_inr: number;
  cost_per_10k_requests: number;
  usd_to_inr_rate: number;
  computed_at: string;
}

export interface VelocityStatus {
  env_name: string;
  current_rps: number;
  slope: number;
  is_spike: boolean;
  baseline_rps: number;
  history: Array<{ timestamp: string; rps: number }>;
}
