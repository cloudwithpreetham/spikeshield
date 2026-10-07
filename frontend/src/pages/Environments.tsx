import { Link } from 'react-router-dom';
import { useEnvironments } from '../hooks/useEnvironments';
import HealthBadge from '../components/shared/HealthBadge';
import LoadingSkeleton from '../components/shared/LoadingSkeleton';
import ErrorBanner from '../components/shared/ErrorBanner';

export default function Environments() {
  const { environments, loading, error } = useEnvironments();

  if (loading && environments.length === 0) return <LoadingSkeleton />;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Environments</h2>
      {error && <ErrorBanner />}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {environments.map(env => {
          const instanceCount = Object.values(env.instances_info || {}).reduce((a, b) => a + b, 0);
          return (
            <Link key={env.env_id || env.env_name} to={`/environments/${env.env_name}`} className="block transition-transform hover:-translate-y-1">
              <div className="card h-full">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold text-white">{env.env_name}</h3>
                  <HealthBadge health={env.health || 'Green'} />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Status</span>
                    <span className="text-gray-300">{env.status}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Instances</span>
                    <span className="text-gray-300 font-medium">{instanceCount}</span>
                  </div>
                  {(env.causes || []).length > 0 && (
                    <div className="mt-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg">
                      <p className="text-xs text-red-400 line-clamp-2">{env.causes[0]}</p>
                    </div>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
        {environments.length === 0 && !loading && (
          <p className="text-gray-500">No environments tracked.</p>
        )}
      </div>
    </div>
  );
}
