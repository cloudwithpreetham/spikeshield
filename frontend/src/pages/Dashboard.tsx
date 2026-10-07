import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store';
import { useEnvironments } from '../hooks/useEnvironments';
import MetricCard from '../components/shared/MetricCard';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import ErrorBanner from '../components/shared/ErrorBanner';
import { formatRPS, formatRelative } from '../utils/format';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const navigate = useNavigate();
  const { environments, loading, error } = useEnvironments();
  const { incidents, metrics } = useStore();

  const activeIncidents = incidents.filter(i => !i.resolved_at);
  const healthyCount = environments.filter(e => e.health === 'Green').length;

  // Aggregate RPS across all environments
  const aggregateMetrics = useMemo(() => {
    const points: Record<string, number> = {};
    Object.values(metrics).forEach(envMetrics => {
      envMetrics.forEach(m => {
        const timeKey = m.timestamp.substring(11, 19); // HH:mm:ss
        points[timeKey] = (points[timeKey] || 0) + m.rps;
      });
    });
    return Object.entries(points).map(([time, rps]) => ({ time, rps })).slice(-60);
  }, [metrics]);

  const totalRPS = aggregateMetrics.length > 0 ? aggregateMetrics[aggregateMetrics.length - 1].rps : 0;

  if (loading && environments.length === 0) return <LoadingSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <div className="flex gap-3">
          <button onClick={() => navigate('/scaling')} className="btn-primary">Pre-Warm Environment</button>
          <button onClick={() => navigate('/blueprint')} className="btn-ghost border border-gray-700">Generate Blueprint</button>
          <button onClick={() => navigate('/chaos')} className="btn-danger">Launch Load Test</button>
        </div>
      </div>

      {error && environments.length === 0 && <ErrorBanner />}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Environments" value={environments.length} />
        <MetricCard title="Healthy" value={healthyCount} subtitle={`${environments.length - healthyCount} unhealthy`} />
        <MetricCard title="Active Incidents" value={activeIncidents.length} trend={activeIncidents.length > 0 ? 'up' : 'neutral'} />
        <MetricCard title="Total RPS" value={formatRPS(totalRPS)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h3 className="text-lg font-medium text-white mb-4">Total Traffic (RPS)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={aggregateMetrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '0.5rem', color: '#f3f4f6' }} />
                <Line type="monotone" dataKey="rps" stroke="#6366f1" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-medium text-white mb-4">Recent Incidents</h3>
          <div className="space-y-4">
            {incidents.slice(0, 5).map(inc => (
              <div key={inc.incident_id} className="border-b border-gray-800 pb-3 last:border-0">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-medium text-white">{inc.env_name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${inc.resolved_at ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'}`}>
                    {inc.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-400 truncate">{inc.description}</p>
                <div className="text-xs text-gray-500 mt-1">{formatRelative(inc.detected_at)}</div>
              </div>
            ))}
            {incidents.length === 0 && <p className="text-gray-500 text-sm">No recent incidents.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
