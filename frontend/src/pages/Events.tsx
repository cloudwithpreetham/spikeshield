import { useState, useEffect } from 'react';
import { getEvents, deleteEvent, createEvent, getPresetEvents, EventCreateRequest } from '../api/endpoints';
import { ScheduledEvent } from '../types';
import { formatIST, formatRelative } from '../utils/format';

export default function Events() {
  const [events, setEvents] = useState<ScheduledEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const data = await getEvents();
      setEvents(data.sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()));
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleAddPreset = async (name: string) => {
    const payload: EventCreateRequest = {
      name,
      type: 'CUSTOM',
      scheduled_at: new Date(Date.now() + 86400000).toISOString(),
      expected_peak_rps: 5000,
      env_name: 'production-env',
      description: 'Preset event'
    };
    try {
      await createEvent(payload);
      loadEvents();
    } catch (e) { console.error(e); }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteEvent(id);
      loadEvents();
    } catch (e) { console.error(e); }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Scheduled Events</h2>
        <button className="btn-primary">Add Event</button>
      </div>

      <div className="card mb-6">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Quick Add Presets</h3>
        <div className="flex gap-3">
          <button onClick={() => handleAddPreset('NEET 2027 Result')} className="badge-gray hover:bg-gray-700 px-3 py-1.5 cursor-pointer text-sm">NEET 2027 Result</button>
          <button onClick={() => handleAddPreset('IPL 2027 Final')} className="badge-gray hover:bg-gray-700 px-3 py-1.5 cursor-pointer text-sm">IPL 2027 Final</button>
          <button onClick={() => handleAddPreset('Diwali Sale 2026')} className="badge-gray hover:bg-gray-700 px-3 py-1.5 cursor-pointer text-sm">Diwali Sale 2026</button>
        </div>
      </div>

      <div className="grid gap-4">
        {loading ? <p className="text-gray-500">Loading events...</p> : events.map(ev => (
          <div key={ev.event_id} className="card flex items-center justify-between border-l-4 border-l-indigo-500">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h3 className="text-lg font-bold text-white">{ev.name}</h3>
                <span className="badge-yellow">{ev.type}</span>
              </div>
              <div className="text-sm text-gray-400 space-x-4">
                <span>Time: {formatIST(ev.scheduled_at)}</span>
                <span>Pre-warm: {formatIST(new Date(new Date(ev.scheduled_at).getTime() - 1800000).toISOString())}</span>
                <span>Env: {ev.env_name}</span>
                <span>Peak RPS: {ev.expected_peak_rps}</span>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-sm text-gray-500">Starts in</div>
                <div className="text-xl font-mono text-indigo-400 font-bold">{formatRelative(ev.scheduled_at).replace('in ', '')}</div>
              </div>
              <button onClick={() => handleDelete(ev.event_id)} className="text-red-400 hover:text-red-300 p-2">Delete</button>
            </div>
          </div>
        ))}
        {!loading && events.length === 0 && <p className="text-gray-500">No upcoming events.</p>}
      </div>
    </div>
  );
}
