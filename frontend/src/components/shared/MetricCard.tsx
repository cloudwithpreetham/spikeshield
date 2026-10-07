export default function MetricCard({ 
  title, 
  value, 
  subtitle, 
  trend, 
  unit 
}: { 
  title: string; 
  value: string | number; 
  subtitle?: string; 
  trend?: 'up' | 'down' | 'neutral';
  unit?: string;
}) {
  return (
    <div className="card flex flex-col gap-2">
      <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-white">{value}</span>
        {unit && <span className="text-gray-500 text-sm">{unit}</span>}
      </div>
      {(subtitle || trend) && (
        <div className="flex items-center gap-2 text-sm">
          {trend === 'up' && <span className="text-green-400">↑</span>}
          {trend === 'down' && <span className="text-red-400">↓</span>}
          {trend === 'neutral' && <span className="text-gray-400">-</span>}
          {subtitle && <span className="text-gray-500">{subtitle}</span>}
        </div>
      )}
    </div>
  );
}
