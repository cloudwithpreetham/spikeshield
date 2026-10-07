import { useState, useEffect } from 'react';
import { getVelocityStatus, triggerPrewarm, simulateSpike } from '../api/endpoints';
import { VelocityStatus } from '../types';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Scaling() {
  const [envName, setEnvName] = useState('production-env');
  const [targetCapacity, setTargetCapacity] = useState(10);
  const [velocity, setVelocity] = useState<VelocityStatus | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getVelocityStatus(envName);
        setVelocity(data);
      } catch (e) {
        console.error(e);
      }
    }
    load();
    const int = setInterval(load, 5000);
    return () => clearInterval(int);
  }, [envName]);

  const handlePrewarm = async () => {
    await triggerPrewarm(envName, targetCapacity);
    alert('Pre-warming triggered');
  };
  const handleSimulate = async () => {
    await simulateSpike(envName);
    alert('Spike simulation triggered');
  };

  const chartData = velocity?.history.map(h => ({ time: h.timestamp.substring(11, 19), rps: h.rps })) || [];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Predictive Scaling</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card col-span-1 flex flex-col items-center justify-center py-10">
          <h3 className="text-sm font-medium text-gray-400 mb-6">Current Velocity</h3>
          <div className="text-6xl font-bold text-white mb-2">
            {velocity?.current_rps || 0}
            <span className="text-xl text-gray-500 ml-2">RPS</span>
          </div>
          <div className="flex items-center gap-2 mt-4">
            <span className={`text-xl ${velocity && velocity.slope > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {velocity && velocity.slope > 0 ? '↗' : '↘'}
            </span>
            <span className="text-gray-400">Slope: {velocity?.slope?.toFixed(2) || 0}</span>
          </div>
          {velocity?.is_spike && (
            <div className="mt-6 px-4 py-1.5 bg-red-900/50 text-red-400 border border-red-800 rounded-full font-bold animate-pulse">
              SPIKE DETECTED
            </div>
          )}
        </div>

        <div className="card col-span-2">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Traffic Trajectory</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorRps" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#f3f4f6' }} />
                <Area type="monotone" dataKey="rps" stroke="#6366f1" fillOpacity={1} fill="url(#colorRps)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-medium text-white mb-4">Manual Scaling Actions</h3>
        <div className="flex items-end gap-4 max-w-2xl">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Environment</label>
            <input type="text" value={envName} onChange={e => setEnvName(e.target.value)} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white" />
          </div>
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Target Capacity: {targetCapacity}</label>
            <input type="range" min="1" max="100" value={targetCapacity} onChange={e => setTargetCapacity(parseInt(e.target.value))} className="w-full accent-indigo-500 mb-2" />
          </div>
          <button onClick={handlePrewarm} className="btn-primary">Pre-Warm Now</button>
          <button onClick={handleSimulate} className="btn-ghost border border-gray-700">Simulate Spike</button>
        </div>
      </div>
    </div>
  );
}
