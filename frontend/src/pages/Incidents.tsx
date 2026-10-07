import { useState } from 'react';
import { useStore } from '../store';
import { triggerRollback, triggerDrain, evaluateHealer } from '../api/endpoints';
import { severityColors, formatIST, formatRelative } from '../utils/format';

export default function Incidents() {
  const incidents = useStore(state => state.incidents);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const activeIncidents = incidents.filter(i => !i.resolved_at);
  const resolvedIncidents = incidents.filter(i => i.resolved_at).slice(0, 10);

  const handleRollback = async (id: string) => {
    try { await triggerRollback(id); setConfirmId(null); } catch (e) { console.error(e); }
  };
  const handleDrain = async (id: string) => { try { await triggerDrain(id); } catch (e) { console.error(e); } };
  const handleHealer = async (envName: string) => { try { await evaluateHealer(envName); } catch (e) { console.error(e); } };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-white">Incident Response</h2>

      <div>
        <h3 className="text-lg font-medium text-white mb-4">Active Incidents ({activeIncidents.length})</h3>
        <div className="space-y-4">
          {activeIncidents.map(inc => (
            <div key={inc.incident_id} className="card border-l-4 border-l-red-500 relative">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className="text-xl font-bold text-white">{inc.env_name}</h4>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${severityColors[inc.severity]}`}>{inc.severity.toUpperCase()}</span>
                    <span className="badge-gray">{inc.type}</span>
                  </div>
                  <p className="text-gray-400">{inc.description}</p>
                </div>
                <div className="text-right text-sm">
                  <div className="text-gray-300 font-medium">{formatRelative(inc.detected_at)}</div>
                  <div className="text-gray-500">{formatIST(inc.detected_at)}</div>
                </div>
              </div>

              {inc.actions_taken.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-gray-500 mb-2">Automated Actions Taken</h5>
                  <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                    {inc.actions_taken.map((action, i) => <li key={i}>{action}</li>)}
                  </ul>
                </div>
              )}

              <div className="flex gap-3 pt-4 border-t border-gray-800">
                {confirmId === inc.incident_id ? (
                  <div className="flex items-center gap-4 bg-red-900/20 p-3 rounded-lg w-full">
                    <span className="text-sm text-red-200">Rollback will swap CNAMEs between production and staging. This cannot be undone automatically. Proceed?</span>
                    <button onClick={() => handleRollback(inc.incident_id)} className="btn-danger whitespace-nowrap">Yes, Rollback</button>
                    <button onClick={() => setConfirmId(null)} className="btn-ghost">Cancel</button>
                  </div>
                ) : (
                  <>
                    <button onClick={() => setConfirmId(inc.incident_id)} className="btn-primary bg-red-600 hover:bg-red-500">Rollback</button>
                    <button onClick={() => handleDrain(inc.incident_id)} className="btn-ghost border border-gray-700">Drain Instances</button>
                    <button onClick={() => handleHealer(inc.env_name)} className="btn-ghost border border-gray-700">Evaluate Healer</button>
                  </>
                )}
              </div>
            </div>
          ))}
          {activeIncidents.length === 0 && (
            <div className="card py-8 text-center border-dashed border-gray-700">
              <span className="text-4xl block mb-2">✅</span>
              <h3 className="text-lg font-medium text-gray-300">No active incidents</h3>
              <p className="text-gray-500 text-sm mt-1">All systems are operating normally.</p>
            </div>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-400 mb-4">Recently Resolved</h3>
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-900/50 text-gray-400 border-b border-gray-800">
              <tr>
                <th className="px-6 py-3 font-medium">Environment</th>
                <th className="px-6 py-3 font-medium">Severity</th>
                <th className="px-6 py-3 font-medium">Description</th>
                <th className="px-6 py-3 font-medium">Resolved</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {resolvedIncidents.map(inc => (
                <tr key={inc.incident_id} className="text-gray-300">
                  <td className="px-6 py-4">{inc.env_name}</td>
                  <td className="px-6 py-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${severityColors[inc.severity]}`}>{inc.severity}</span>
                  </td>
                  <td className="px-6 py-4">{inc.description}</td>
                  <td className="px-6 py-4 text-gray-500">{formatRelative(inc.resolved_at!)}</td>
                </tr>
              ))}
              {resolvedIncidents.length === 0 && <tr><td colSpan={4} className="px-6 py-8 text-center text-gray-500">No resolved incidents in history.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
