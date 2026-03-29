export function EmptyState({ onClear, hasFilters = false }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.05] to-white/[0.015] p-8 text-center shadow-card backdrop-blur-sm">
      <div className="mx-auto mb-5 grid h-14 w-14 place-items-center rounded-2xl border border-white/15 bg-accent-500/10 text-accent-300">
        <span className="text-xl">~</span>
      </div>
      <h2 className="text-lg font-semibold text-slate-100">No matching pain points</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
        {hasFilters
          ? "Your current filters are too narrow. Reset controls to see the full intelligence feed."
          : "Run ingestion or connect backend data to populate this dashboard feed."}
      </p>
      {hasFilters ? (
        <button
          type="button"
          onClick={onClear}
          className="mt-5 rounded-full border border-accent-300/55 bg-accent-500/15 px-5 py-2 text-sm font-semibold text-accent-200 transition-colors hover:bg-accent-500/30"
        >
          Reset controls
        </button>
      ) : null}
    </section>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <section className="rounded-3xl border border-rose-400/35 bg-gradient-to-b from-rose-900/35 to-rose-950/25 p-8 text-center shadow-card">
      <h2 className="text-lg font-semibold text-rose-100">Could not load the feed</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-rose-200/85">{message || "Unexpected error"}</p>
      <button
        type="button"
        className="mt-5 rounded-full border border-accent-300/55 bg-accent-500/15 px-5 py-2 text-sm font-semibold text-accent-200 transition-colors hover:bg-accent-500/30"
        onClick={onRetry}
      >
        Retry
      </button>
    </section>
  );
}
