export default function Loading() {
  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      {/* Header skeleton */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="space-y-2">
          <div className="h-8 w-32 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
          <div className="h-4 w-48 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
        </div>
        <div className="h-10 w-24 bg-slate-200 dark:bg-slate-800 rounded-full animate-shimmer-slide" />
      </div>

      {/* Mood trend skeleton */}
      <div className="rounded-[2rem] border-none bg-background/60 backdrop-blur-xl shadow-xl shadow-black/5 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 w-32 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
          <div className="h-8 w-8 bg-slate-200 dark:bg-slate-800 rounded-full animate-shimmer-slide" />
        </div>
        <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded-xl animate-shimmer-slide" />
      </div>

      {/* Search and filter skeleton */}
      <div className="rounded-[2rem] border-none bg-background/60 backdrop-blur-xl shadow-lg shadow-black/5 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 w-40 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
          <div className="h-8 w-8 bg-slate-200 dark:bg-slate-800 rounded-full animate-shimmer-slide" />
        </div>
        <div className="flex gap-4 mb-4">
          <div className="flex-1 h-10 bg-slate-200 dark:bg-slate-800 rounded-xl animate-shimmer-slide" />
          <div className="h-10 w-24 bg-slate-200 dark:bg-slate-800 rounded-full animate-shimmer-slide" />
          <div className="h-10 w-20 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
        </div>
      </div>

      {/* Journal entries skeleton */}
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="rounded-2xl border p-6 space-y-3 bg-background/60 backdrop-blur-xl shadow-xl shadow-black/5">
            <div className="h-5 w-40 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
            <div className="h-4 w-full bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
            <div className="h-4 w-3/4 bg-slate-200 dark:bg-slate-800 rounded-md animate-shimmer-slide" />
            <div className="flex gap-2 pt-2">
              <div className="h-6 w-16 bg-slate-200 dark:bg-slate-800 rounded-full animate-shimmer-slide" />
              <div className="h-6 w-20 bg-slate-200 dark:bg-slate-800 rounded-full animate-shimmer-slide" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}