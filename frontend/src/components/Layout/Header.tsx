import { useEffect, useState } from 'react';
import { useStore } from '../../store';
import { format } from 'date-fns';

export default function Header() {
  const wsConnected = useStore((state) => state.wsConnected);
  const lastUpdated = useStore((state) => state.lastUpdated);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6 fixed top-0 right-0 left-64 z-10">
      <div className="flex items-center gap-3 text-sm text-gray-400">
        <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span>{wsConnected ? 'Live' : 'Reconnecting...'}</span>
        {lastUpdated && <span>• Last updated: {format(lastUpdated, 'HH:mm:ss')}</span>}
      </div>
      <div className="text-gray-300 font-mono text-sm">
        {format(time, 'dd MMM yyyy, HH:mm:ss')} IST
      </div>
    </header>
  );
}
