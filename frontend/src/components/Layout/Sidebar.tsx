import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Server, Layers, Calendar, TrendingUp, Zap, IndianRupee, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/environments', icon: Server, label: 'Environments' },
  { to: '/blueprint', icon: Layers, label: 'Blueprint Gen' },
  { to: '/events', icon: Calendar, label: 'Events' },
  { to: '/scaling', icon: TrendingUp, label: 'Scaling' },
  { to: '/chaos', icon: Zap, label: 'Chaos Test' },
  { to: '/finops', icon: IndianRupee, label: 'FinOps' },
  { to: '/incidents', icon: AlertTriangle, label: 'Incidents' },
];

export default function Sidebar() {
  return (
    <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-screen fixed">
      <div className="p-6 flex items-center gap-3 border-b border-gray-800">
        <span className="text-3xl">🛡️</span>
        <h1 className="text-xl font-bold text-white tracking-tight">SpikeShield</h1>
      </div>
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors',
                isActive ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
