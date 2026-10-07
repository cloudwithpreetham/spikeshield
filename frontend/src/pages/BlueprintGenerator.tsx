import { useState } from 'react';
import { generateBlueprint, getBlueprintTemplate } from '../api/endpoints';
import { WorkloadProfile, BlueprintRequest, BlueprintResult } from '../types';
import JSZip from 'jszip';

const profiles = [
  { id: 'HIGH_CONCURRENCY_UPI', icon: '🚀', name: 'UPI Payment Webhooks', desc: 'Optimized for 10k TPS payment callbacks, strict SLA, keepalive tuning' },
  { id: 'EDTECH_RESULT_PORTAL', icon: '📚', name: 'Exam Result Portal', desc: 'Handles 100x sudden traffic on NEET/JEE result day, micro-caching enabled' },
  { id: 'D2C_FLASH_SALE', icon: '🛒', name: 'D2C Flash Sale', desc: 'Diwali/Big Billion Days storefront with checkout rate limiting' },
  { id: 'GENERIC_WEB', icon: '🌐', name: 'Generic Web App', desc: 'Balanced defaults for standard web applications' }
];

export default function BlueprintGenerator() {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<BlueprintRequest | null>(null);
  const [result, setResult] = useState<BlueprintResult | null>(null);
  const [activeTab, setActiveTab] = useState('nginx.conf');

  const handleProfileSelect = async (profileId: string) => {
    try {
      const template = await getBlueprintTemplate(profileId as WorkloadProfile);
      setConfig(template);
      setStep(2);
    } catch (e) {
      console.error(e);
      // Fallback if API is down
      setConfig({
        profile: profileId as WorkloadProfile, app_port: 8080, worker_processes: 4, max_connections: 4096,
        enable_rate_limiting: false, rate_limit_rps: 100, enable_gzip: true, enable_brotli: false,
        enable_imdsv2: true, instance_type: 't3.large', min_instances: 2, max_instances: 10,
        enable_spot: true, spot_max_price: '0.05', custom_env_vars: {}
      });
      setStep(2);
    }
  };

  const handleGenerate = async () => {
    if (!config) return;
    try {
      const res = await generateBlueprint(config);
      setResult(res);
      setStep(3);
    } catch (e) {
      console.error(e);
      // Fallback
      setResult({
        profile: config.profile,
        nginx_config: '# nginx configuration\nworker_processes ' + config.worker_processes + ';',
        ebextension_capacity: 'option_settings:\n  aws:autoscaling:asg:\n    MinSize: ' + config.min_instances,
        ebextension_cloudwatch: '', ebextension_security: '', platform_predeploy_hook: '',
        platform_postdeploy_hook: '', procfile: 'web: npm start', generated_at: new Date().toISOString()
      });
      setStep(3);
    }
  };

  const downloadZip = async () => {
    if (!result) return;
    const zip = new JSZip();
    zip.file('.platform/nginx/nginx.conf', result.nginx_config);
    zip.file('.ebextensions/01_capacity.config', result.ebextension_capacity);
    zip.file('.ebextensions/02_cloudwatch.config', result.ebextension_cloudwatch);
    zip.file('.ebextensions/03_security.config', result.ebextension_security);
    zip.file('.platform/hooks/predeploy/01_hook.sh', result.platform_predeploy_hook);
    zip.file('.platform/hooks/postdeploy/01_hook.sh', result.platform_postdeploy_hook);
    zip.file('Procfile', result.procfile);
    const blob = await zip.generateAsync({ type: 'blob' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `spikeshield-blueprint-${result.profile}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: 'nginx.conf', content: result?.nginx_config, type: 'nginx' },
    { id: '01_capacity.config', content: result?.ebextension_capacity, type: 'yaml' },
    { id: '02_cloudwatch.config', content: result?.ebextension_cloudwatch, type: 'yaml' },
    { id: '03_security.config', content: result?.ebextension_security, type: 'yaml' },
    { id: 'predeploy.sh', content: result?.platform_predeploy_hook, type: 'bash' },
    { id: 'postdeploy.sh', content: result?.platform_postdeploy_hook, type: 'bash' },
    { id: 'Procfile', content: result?.procfile, type: 'text' }
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold text-white">Blueprint Generator</h2>
        <div className="flex gap-2">
          {[1, 2, 3].map(i => (
            <div key={i} className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${step >= i ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-500'}`}>
              {i}
            </div>
          ))}
        </div>
      </div>

      {step === 1 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {profiles.map(p => (
            <button key={p.id} onClick={() => handleProfileSelect(p.id)} className="card text-left hover:border-indigo-500 transition-colors group">
              <div className="text-4xl mb-4">{p.icon}</div>
              <h3 className="text-lg font-bold text-white mb-2 group-hover:text-indigo-400">{p.name}</h3>
              <p className="text-sm text-gray-400">{p.desc}</p>
            </button>
          ))}
        </div>
      )}

      {step === 2 && config && (
        <div className="card space-y-6">
          <h3 className="text-xl font-medium text-white mb-4">Configure {config.profile.replace(/_/g, ' ')}</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Worker Processes</label>
                <input type="range" min="1" max="16" value={config.worker_processes} onChange={e => setConfig({ ...config, worker_processes: parseInt(e.target.value) })} className="w-full accent-indigo-500" />
                <div className="text-right text-xs text-gray-500">{config.worker_processes}</div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Max Connections</label>
                <input type="number" min="256" max="8192" value={config.max_connections} onChange={e => setConfig({ ...config, max_connections: parseInt(e.target.value) })} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white" />
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                <span className="text-sm text-gray-300">Enable Rate Limiting</span>
                <input type="checkbox" checked={config.enable_rate_limiting} onChange={e => setConfig({ ...config, enable_rate_limiting: e.target.checked })} className="w-4 h-4 text-indigo-600 rounded bg-gray-700 border-gray-600" />
              </div>
              {config.enable_rate_limiting && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Rate Limit (RPS)</label>
                  <input type="number" value={config.rate_limit_rps} onChange={e => setConfig({ ...config, rate_limit_rps: parseInt(e.target.value) })} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white" />
                </div>
              )}
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Instance Type</label>
                <select value={config.instance_type} onChange={e => setConfig({ ...config, instance_type: e.target.value })} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white">
                  <option value="t3.medium">t3.medium</option>
                  <option value="t3.large">t3.large</option>
                  <option value="m5.large">m5.large</option>
                  <option value="c5.large">c5.large</option>
                </select>
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm text-gray-400 mb-1">Min Instances</label>
                  <input type="number" value={config.min_instances} onChange={e => setConfig({ ...config, min_instances: parseInt(e.target.value) })} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white" />
                </div>
                <div className="flex-1">
                  <label className="block text-sm text-gray-400 mb-1">Max Instances</label>
                  <input type="number" value={config.max_instances} onChange={e => setConfig({ ...config, max_instances: parseInt(e.target.value) })} className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white" />
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                <span className="text-sm text-gray-300">Enable Spot Instances</span>
                <input type="checkbox" checked={config.enable_spot} onChange={e => setConfig({ ...config, enable_spot: e.target.checked })} className="w-4 h-4 text-indigo-600 rounded bg-gray-700 border-gray-600" />
              </div>
            </div>
          </div>
          
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-800">
            <button onClick={() => setStep(1)} className="btn-ghost">Back</button>
            <button onClick={handleGenerate} className="btn-primary">Generate Blueprints</button>
          </div>
        </div>
      )}

      {step === 3 && result && (
        <div className="card">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-medium text-white">Generated Configurations</h3>
            <div className="flex gap-2">
              <button onClick={() => setStep(2)} className="btn-ghost">Edit Config</button>
              <button onClick={downloadZip} className="btn-primary">Download All as ZIP</button>
            </div>
          </div>
          
          <div className="flex gap-2 border-b border-gray-800 overflow-x-auto pb-2 mb-4">
            {tabs.map(t => t.content ? (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg whitespace-nowrap transition-colors ${activeTab === t.id ? 'bg-indigo-600/20 text-indigo-400' : 'text-gray-400 hover:bg-gray-800'}`}
              >
                {t.id}
              </button>
            ) : null)}
          </div>
          
          <div className="relative group">
            <button 
              onClick={() => {
                const content = tabs.find(t => t.id === activeTab)?.content;
                if (content) navigator.clipboard.writeText(content);
              }} 
              className="absolute top-4 right-4 bg-gray-800 text-gray-300 hover:text-white px-3 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity"
            >
              Copy
            </button>
            <pre className={`p-4 rounded-xl bg-[#0d1117] overflow-x-auto text-sm font-mono border border-gray-800 ${
              tabs.find(t => t.id === activeTab)?.type === 'nginx' ? 'text-green-300' : 'text-yellow-200'
            }`}>
              {tabs.find(t => t.id === activeTab)?.content || 'No content generated.'}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
