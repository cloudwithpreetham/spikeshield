import { useState, useEffect } from 'react';
import { getFinOpsSummary, getFinOps } from '../api/endpoints';
import { formatINR } from '../utils/format';
import MetricCard from '../components/shared/MetricCard';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function FinOps() {
  const [summary, setSummary] = useState<any>(null);
  const [envData, setEnvData] = useState<any[]>([]);

  const loadData = async () => {
    try {
      const sum = await getFinOpsSummary();
      setSummary(sum);
      // Fetch detailed data for charts if envs exist
      if (sum.total_envs > 0) {
        // mock/example data for chart if detailed endpoint not used for this simple view
        setEnvData([
          { name: 'production-env', cost: 1200 },
          { name: 'staging-env', cost: 300 }
        ]);
      }
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">FinOps Dashboard</h2>
        <button onClick={loadData} className="btn-ghost border border-gray-700">Refresh</button>
      </div>

      <div className="text-sm text-gray-500 text-right mb-2">Exchange Rate: $1 USD = INR 84.00</div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total INR/hr" value={formatINR(summary?.total_hourly_inr || 0)} />
        <MetricCard title="On-Demand INR/hr" value={formatINR(summary?.ondemand_hourly_inr || 0)} />
        <MetricCard title="Spot INR/hr" value={formatINR(summary?.spot_hourly_inr || 0)} />
        <MetricCard title="INR per 10k requests" value={formatINR(1.25)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2 h-80">
          <h3 className="text-lg font-medium text-white mb-4">Cost by Environment (INR/hr)</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={envData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#f3f4f6' }} />
              <Bar dataKey="cost" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="space-y-6">
          <div className="card bg-indigo-900/20 border-indigo-900/50">
            <h3 className="text-lg font-medium text-indigo-400 mb-2">Spot Instance Savings</h3>
            <p className="text-gray-300 text-sm mb-4">If 50% Spot: save {formatINR(2500)} INR/day</p>
            <div className="w-full bg-gray-800 rounded-full h-2">
              <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '45%' }}></div>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-right">45% Spot Coverage</div>
          </div>
          
          <div className="card">
            <h3 className="text-lg font-medium text-white mb-4">Projections</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-end border-b border-gray-800 pb-2">
                <span className="text-gray-400">Daily Run Rate</span>
                <span className="text-xl font-bold text-white">{formatINR(summary?.total_daily_inr || 0)}</span>
              </div>
              <div className="flex justify-between items-end">
                <span className="text-gray-400">Monthly Run Rate</span>
                <span className="text-xl font-bold text-white">{formatINR((summary?.total_daily_inr || 0) * 30)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
