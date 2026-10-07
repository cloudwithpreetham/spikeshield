import { create } from 'zustand';
import type { EnvironmentHealth, IncidentEvent, MetricsSnapshot, ScheduledEvent } from '../types';

interface SpikeShieldStore {
  environments: EnvironmentHealth[];
  incidents: IncidentEvent[];
  metrics: Record<string, MetricsSnapshot[]>; // env_name -> time series
  events: ScheduledEvent[];
  wsConnected: boolean;
  lastUpdated: Date | null;
  setEnvironments: (envs: EnvironmentHealth[]) => void;
  setIncidents: (incidents: IncidentEvent[]) => void;
  addMetricsSnapshot: (snapshot: MetricsSnapshot) => void;
  setEvents: (events: ScheduledEvent[]) => void;
  setWsConnected: (connected: boolean) => void;
  setLastUpdated: (date: Date) => void;
}

export const useStore = create<SpikeShieldStore>((set) => ({
  environments: [],
  incidents: [],
  metrics: {},
  events: [],
  wsConnected: false,
  lastUpdated: null,
  setEnvironments: (environments) => set({ environments }),
  setIncidents: (incidents) => set({ incidents }),
  addMetricsSnapshot: (snapshot) => set((state) => {
    const history = state.metrics[snapshot.env_name] ?? [];
    const updated = [...history.slice(-59), snapshot]; // keep 60 points
    return { metrics: { ...state.metrics, [snapshot.env_name]: updated }, lastUpdated: new Date() };
  }),
  setEvents: (events) => set({ events }),
  setWsConnected: (wsConnected) => set({ wsConnected }),
  setLastUpdated: (lastUpdated) => set({ lastUpdated }),
}));
