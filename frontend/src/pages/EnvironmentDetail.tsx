import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getEnvironmentDetail, getEnvironmentInstances, getEnvironmentEvents } from '../api/endpoints';
import { EnvironmentDetail as EnvDetailType } from '../types';
import HealthBadge from '../components/shared/HealthBadge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useStore } from '../store';
import { formatIST } from '../utils/format';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';

export default function EnvironmentDetail() {
  const { envName } = useParams<{ envName: string }>();
  const [detail, setDetail] = useState<EnvDetailType | null>(null);
  const [instances, setInstances] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('Overview');
  const [loading, setLoading] = useState(true);
  
  const metricsData = useStore(state => state.metrics[envName || ''] || []);

  useEffect(() => {
    if (!envName) return;
    async function loadData() {
      try {
        setLoading(true);
        const [d, inst, evs] = await Promise.all([
          getEnvironmentDetail(envName!),
          getEnvironmentInstances(envName!),
          getEnvironmentEvents(envName!)
        ]);
        setDetail(d); setInstances(inst); setEvents(evs);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [envName]);

  if (loading) return <LoadingSkeleton />;
  if (!detail) return <p className="text-gray-500">Environment not found.</p>;

  const chartData = metricsData.map(m => ({ ...m, time: m.timestamp.substring(11, 19) }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">{detail.env_name}</h2>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <HealthBadge health={detail.health} />
            <span>Status: {detail.status}</span>
            <a href={detail.endpoint_url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">
              {detail.cname}
            </a>
          </div>
        </div>
      </div>

      <div className="flex gap-4 border-b border-gray-800">
        {['Overview', 'Metrics', 'Instances', 'Events'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${activeTab === tab ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-gray-500 hover:text-gray-300'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-medium text-white mb-4">Configuration</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Platform</span><span className="text-gray-300 text-right">{detail.solution_stack}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Tier</span><span className="text-gray-300">{detail.tier}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Created At</span><span className="text-gray-300">{formatIST(detail.created_at)}</span></div>
            </div>
          </div>
          {detail.causes && detail.causes.length > 0 && (
            <div className="card border-red-900/50 bg-red-900/10">
              <h3 className="text-lg font-medium text-red-400 mb-4">Health Issues</h3>
              <ul className="list-disc list-inside space-y-2 text-sm text-gray-300">
                {detail.causes.map((cause, i) => <li key={i}>{cause}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === 'Metrics' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { key: 'rps', label: 'Requests/sec', color: '#6366f1' },
            { key: 'p99_latency_ms', label: 'p99 Latency (ms)', color: '#f59e0b' },
            { key: 'cpu_percent', label: 'CPU %', color: '#10b981' },
            { key: 'five_xx_rate', label: '5xx Rate %', color: '#ef4444' }
          ].map(metric => (
            <div key={metric.key} className="card h-72">
              <h3 className="text-sm font-medium text-gray-400 mb-4">{metric.label}</h3>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                  <YAxis stroke="#9ca3af" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#f3f4f6' }} />
                  <Line type="monotone" dataKey={metric.key} stroke={metric.color} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'Instances' && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-gray-400 border-b border-gray-800">
              <tr>
                <th className="pb-3 font-medium">Instance ID</th>
                <th className="pb-3 font-medium">Type</th>
                <th className="pb-3 font-medium">AZ</th>
                <th className="pb-3 font-medium">Health</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {instances.map((inst, i) => (
                <tr key={i} className="text-gray-300">
                  <td className="py-3">{inst.id || 'N/A'}</td>
                  <td className="py-3">{inst.instance_type || 'N/A'}</td>
                  <td className="py-3">{inst.availability_zone || 'N/A'}</td>
                  <td className="py-3"><HealthBadge health={inst.health || 'Green'} /></td>
                </tr>
              ))}
              {instances.length === 0 && <tr><td colSpan={4} className="py-4 text-center text-gray-500">No instances found</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'Events' && (
        <div className="card space-y-4">
          {events.map((ev, i) => (
            <div key={i} className="flex gap-4 border-b border-gray-800 pb-4 last:border-0">
              <div className="text-sm text-gray-500 whitespace-nowrap">{formatIST(ev.event_date)}</div>
              <div>
                <span className={`text-xs px-2 py-0.5 rounded-full mb-1 inline-block ${ev.severity === 'ERROR' ? 'bg-red-900/30 text-red-400' : 'bg-gray-800 text-gray-300'}`}>
                  {ev.severity}
                </span>
                <p className="text-sm text-gray-300">{ev.message}</p>
              </div>
            </div>
          ))}
          {events.length === 0 && <p className="text-gray-500">No events found.</p>}
        </div>
      )}
    </div>
  );
}
