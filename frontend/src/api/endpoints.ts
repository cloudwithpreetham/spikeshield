import { apiClient } from './client';
import type {
  EnvironmentHealth,
  EnvironmentDetail,
  MetricsSnapshot,
  VelocityStatus,
  BlueprintRequest,
  BlueprintResult,
  ScheduledEvent,
  IncidentEvent,
  EnvironmentCost,
  WorkloadProfile,
  EventType
} from '../types';

export interface EventCreateRequest {
  name: string;
  type: EventType;
  scheduled_at: string;
  expected_peak_rps: number;
  env_name: string;
  description: string;
}

export async function getEnvironments(): Promise<EnvironmentHealth[]> {
  const res = await apiClient.get<EnvironmentHealth[]>('/environments');
  return res.data;
}

export async function getEnvironmentDetail(envName: string): Promise<EnvironmentDetail> {
  const res = await apiClient.get<EnvironmentDetail>(`/environments/${envName}`);
  return res.data;
}

export async function getEnvironmentMetrics(envName: string): Promise<MetricsSnapshot> {
  const res = await apiClient.get<MetricsSnapshot>(`/environments/${envName}/metrics`);
  return res.data;
}

export async function getEnvironmentHealth(envName: string): Promise<EnvironmentHealth> {
  const res = await apiClient.get<EnvironmentHealth>(`/environments/${envName}/health`);
  return res.data;
}

export async function getEnvironmentInstances(envName: string): Promise<any[]> {
  const res = await apiClient.get<any[]>(`/environments/${envName}/instances`);
  return res.data;
}

export async function getEnvironmentEvents(envName: string): Promise<any[]> {
  const res = await apiClient.get<any[]>(`/environments/${envName}/events`);
  return res.data;
}

export async function getVelocityStatus(envName: string): Promise<VelocityStatus> {
  const res = await apiClient.get<VelocityStatus>(`/scaling/velocity/${envName}`);
  return res.data;
}

export async function getVelocityHistory(envName: string): Promise<VelocityStatus> {
  const res = await apiClient.get<VelocityStatus>(`/scaling/velocity/${envName}`);
  return res.data;
}

export async function triggerPrewarm(envName: string, targetCapacity: number): Promise<any> {
  const res = await apiClient.post('/scaling/prewarm', {
    env_name: envName,
    target_capacity: targetCapacity
  });
  return res.data;
}

export async function simulateSpike(envName: string): Promise<any> {
  const res = await apiClient.post('/scaling/simulate-spike', { env_name: envName });
  return res.data;
}

export async function generateBlueprint(request: BlueprintRequest): Promise<BlueprintResult> {
  const res = await apiClient.post<BlueprintResult>('/blueprints/generate', request);
  return res.data;
}

export async function getBlueprintProfiles(): Promise<any[]> {
  const res = await apiClient.get<any[]>('/blueprints/profiles');
  return res.data;
}

export async function getBlueprintTemplate(profile: WorkloadProfile): Promise<BlueprintRequest> {
  const res = await apiClient.get<BlueprintRequest>(`/blueprints/templates/${profile}`);
  return res.data;
}

export async function getEvents(): Promise<ScheduledEvent[]> {
  const res = await apiClient.get<ScheduledEvent[]>('/events');
  return res.data;
}

export async function createEvent(req: EventCreateRequest): Promise<ScheduledEvent> {
  const res = await apiClient.post<ScheduledEvent>('/events', req);
  return res.data;
}

export async function deleteEvent(eventId: string): Promise<void> {
  await apiClient.delete(`/events/${eventId}`);
}

export async function getUpcomingEvents(): Promise<ScheduledEvent[]> {
  const res = await apiClient.get<ScheduledEvent[]>('/events/upcoming');
  return res.data;
}

export async function getPresetEvents(): Promise<any[]> {
  const res = await apiClient.get<any[]>('/events/presets');
  return res.data;
}

export async function getIncidents(): Promise<IncidentEvent[]> {
  const res = await apiClient.get<IncidentEvent[]>('/incidents');
  return res.data;
}

export async function triggerRollback(incidentId: string): Promise<any> {
  const res = await apiClient.post(`/incidents/${incidentId}/rollback`);
  return res.data;
}

export async function triggerDrain(incidentId: string): Promise<any> {
  const res = await apiClient.post(`/incidents/${incidentId}/drain`);
  return res.data;
}

export async function evaluateHealer(envName: string): Promise<any> {
  const res = await apiClient.post(`/incidents/evaluate/${envName}`);
  return res.data;
}

export async function getFinOps(envName: string): Promise<EnvironmentCost> {
  const res = await apiClient.get<EnvironmentCost>(`/finops/${envName}`);
  return res.data;
}

export async function getFinOpsSummary(): Promise<any> {
  const res = await apiClient.get<any>('/finops/summary');
  return res.data;
}

export async function getFinOpsUnitEconomics(envName: string): Promise<any> {
  const res = await apiClient.get<any>(`/finops/unit-economics/${envName}`);
  return res.data;
}

export async function startChaosSpike(payload: {target_url: string, duration_seconds: number, concurrent_users: number, ramp_up_seconds: number}): Promise<{job_id: string}> {
  const res = await apiClient.post<{job_id: string}>('/chaos/spike', payload);
  return res.data;
}

export async function getChaosStatus(jobId: string): Promise<any> {
  const res = await apiClient.get<any>(`/chaos/status/${jobId}`);
  return res.data;
}

export async function stopChaos(jobId: string): Promise<void> {
  await apiClient.post(`/chaos/stop/${jobId}`);
}

export async function sendSlackTest(): Promise<any> {
  const res = await apiClient.post('/alerts/slack/test');
  return res.data;
}
