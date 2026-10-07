import { HealthColor } from '../../types';
import clsx from 'clsx';

export default function HealthBadge({ health }: { health: HealthColor | string }) {
  const getBadgeStyles = () => {
    switch (health) {
      case 'Green': return 'badge-green';
      case 'Yellow': return 'badge-yellow';
      case 'Red': return 'badge-red';
      default: return 'badge-gray';
    }
  };

  return (
    <span className={clsx('inline-flex items-center gap-1.5', getBadgeStyles())}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {health}
    </span>
  );
}
