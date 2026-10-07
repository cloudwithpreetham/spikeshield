import { AlertTriangle } from 'lucide-react';

export default function ErrorBanner({ url }: { url?: string }) {
  const displayUrl = url || (typeof window !== 'undefined' ? window.location.origin : 'backend');
  return (
    <div className="bg-red-900/30 border border-red-800 p-4 rounded-xl flex items-start gap-3 mb-6 text-red-200">
      <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
      <div>
        <h4 className="font-semibold text-red-400">Connection Error</h4>
        <p className="text-sm mt-1">
          Cannot connect to SpikeShield API at {displayUrl}. Ensure backend service is running.
        </p>
      </div>
    </div>
  );
}
