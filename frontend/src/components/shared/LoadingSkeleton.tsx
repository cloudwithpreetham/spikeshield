export default function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="card animate-pulse h-32 flex flex-col gap-4">
          <div className="h-4 bg-gray-800 rounded w-1/3"></div>
          <div className="h-8 bg-gray-800 rounded w-1/2"></div>
          <div className="h-4 bg-gray-800 rounded w-2/3 mt-auto"></div>
        </div>
      ))}
    </div>
  );
}
