import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { getEnvironments } from '../api/endpoints';
export function useEnvironments() {
  const { environments, setEnvironments } = useStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    async function load() {
      try { setLoading(true); const envs = await getEnvironments(); setEnvironments(envs); setError(null); }
      catch (e: any) { setError(e.message); }
      finally { setLoading(false); }
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [setEnvironments]);
  return { environments, loading, error };
}
