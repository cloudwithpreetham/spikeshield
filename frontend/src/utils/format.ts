import { format, formatDistanceToNow } from 'date-fns';
export function formatIST(dateStr: string): string {
  // Format as '07 Oct 2026, 02:00 PM IST'
  try { return format(new Date(dateStr), 'dd MMM yyyy, hh:mm a') + ' IST'; }
  catch { return dateStr; }
}
export function formatRelative(dateStr: string): string {
  try { return formatDistanceToNow(new Date(dateStr), { addSuffix: true }); }
  catch { return dateStr; }
}
export function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 }).format(amount);
}
export function formatRPS(rps: number): string {
  if (rps >= 1000) return (rps / 1000).toFixed(1) + 'k RPS';
  return rps.toFixed(0) + ' RPS';
}
export const healthColors: Record<string, string> = {
  Green: 'text-green-400',
  Yellow: 'text-yellow-400',
  Red: 'text-red-400',
  Grey: 'text-gray-400',
};
export const severityColors: Record<string, string> = {
  critical: 'text-red-400 bg-red-900/30 border-red-800',
  high: 'text-orange-400 bg-orange-900/30 border-orange-800',
  medium: 'text-yellow-400 bg-yellow-900/30 border-yellow-800',
  low: 'text-blue-400 bg-blue-900/30 border-blue-800',
};
