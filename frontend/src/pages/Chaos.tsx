import { useState, useEffect } from 'react';
import { startChaosSpike, getChaosStatus, stopChaos } from '../api/endpoints';
import { AlertTriangle } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis } from 'recharts';

export default function Chaos() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [form, setForm] = useState({
    target_url: 'http://localhost:8000/health',
    duration_seconds: 60,
    concurrent_users: 50,
    ramp_up_seconds: 10
  });

  useEffect(() => {
    let int: any;
    if (jobId) {
      int = setInterval(async () => {
        try {
          const res = await getChaosStatus(jobId);
          setStatus(res);
          if (res.status === 'completed' || res.status === 'failed' || res.status === 'stopped') {
            clearInterval(int);
            setJobId(null);
          }
        } catch (e) {
          console.error(e);
        }
      }, 2000);
    }
    return () => clearInterval(int);
  }, [jobId]);

  const handleLaunch = async () => {
    try {
      const res = await startChaosSpike(form);
      setJobId(res.job_id);
      setStatus(null);
    } catch (e) { console.error(e); }
  };

  const handleStop = async () => {
    if (jobId) await stopChaos(jobId);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-white">Chaos Load Tester</h2>

      <div className="bg-yellow-900/30 border border-yellow-800 p-4 rounded-xl flex items-start gap-3 text-yellow-200">
        <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-yellow-500">Warning</h4>
          <p className="text-sm mt-1">This will generate real traffic to the target URL. Use responsibly against staging environments only.</p>
        </div>
      </div>

      <div className="card space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-400 mb-1">Target URL</label>
            <input type="text" value={form.target_url} onChange={e => setForm({...form, target_url: e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white font-mono" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Duration: {form.duration_seconds}s</label>
            <input type="range" min="30" max="300" value={form.duration_seconds} onChange={e => setForm({...form, duration_seconds: parseInt(e.target.value)})} className="w-full accent-indigo-500" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Concurrent Users</label>
            <input type="number" min="10" max="1000" value={form.concurrent_users} onChange={e => setForm({...form, concurrent_users: parseInt(e.target.value)})} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white" />
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-800">
          <button onClick={handleLaunch} disabled={!!jobId} className="btn-danger disabled:opacity-50 disabled:cursor-not-allowed">Launch Load Test</button>
        </div>
      </div>

      {status && (
        <div className="card">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-medium text-white">Live Execution: {status.job_id}</h3>
            <div className="flex items-center gap-4">
              <span className={`text-sm px-2 py-1 rounded-full uppercase font-bold ${status.status === 'running' ? 'bg-indigo-900/50 text-indigo-400 animate-pulse' : 'bg-gray-800 text-gray-400'}`}>
                {status.status}
              </span>
              {status.status === 'running' && <button onClick={handleStop} className="text-red-400 text-sm hover:underline">Stop</button>}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400">Current RPS</div>
              <div className="text-3xl font-bold text-white mt-1">{status.current_rps || 0}</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400">Error Rate</div>
              <div className="text-3xl font-bold text-red-400 mt-1">{status.error_rate_percent?.toFixed(1) || 0}%</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-4 text-center">
              <div className="text-sm text-gray-400">Avg Latency</div>
              <div className="text-3xl font-bold text-yellow-400 mt-1">{status.avg_latency_ms?.toFixed(0) || 0}ms</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
