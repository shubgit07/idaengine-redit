import Badge from "@/components/Badge";
import { SORT_OPTIONS, SEVERITY_OPTIONS } from "@/lib/dashboardControls";

function FilterChip({ label, active, onClick, count }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors",
        active
          ? "border-accent-300/60 bg-accent-500/18 text-accent-200"
          : "border-white/15 bg-white/[0.03] text-slate-300 hover:border-white/30 hover:bg-white/[0.07]",
      ].join(" ")}
    >
      <span>{label}</span>
      {typeof count === "number" ? <span className="text-[10px] text-slate-400">{count}</span> : null}
    </button>
  );
}

export default function ControlsBar({
  value,
  categories,
  total,
  filteredTotal,
  onSearchChange,
  onSortChange,
  onToggleCategory,
  onToggleSeverity,
  onClear,
}) {
  return (
    <section className="mb-6 rounded-3xl border border-white/10 bg-slate-900/45 p-4 shadow-card backdrop-blur-sm sm:p-5">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Controls</p>
          <p className="mt-1 text-sm text-slate-300">
            Showing <span className="font-semibold text-slate-100">{filteredTotal}</span> of {total} results
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">URL Synced</Badge>
          <button
            type="button"
            className="rounded-full border border-white/15 px-3 py-1.5 text-xs font-semibold text-slate-300 transition-colors hover:border-white/30 hover:bg-white/[0.06]"
            onClick={onClear}
          >
            Clear filters
          </button>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1.5fr_auto]">
        <label className="relative block">
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Search</span>
          <input
            type="search"
            value={value.search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Search title, issue, subreddit, category"
            className="w-full rounded-2xl border border-white/15 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-500 focus:border-accent-400/70 focus:bg-white/[0.05]"
          />
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Sort</span>
          <select
            value={value.sort}
            onChange={(event) => onSortChange(event.target.value)}
            className="w-full min-w-[210px] rounded-2xl border border-white/15 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-100 outline-none transition-colors focus:border-accent-400/70"
          >
            <option value={SORT_OPTIONS.latest}>Latest</option>
            <option value={SORT_OPTIONS.highest_score}>Highest score</option>
          </select>
        </label>
      </div>

      <div className="mt-4 grid gap-4">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Severity</p>
          <div className="flex flex-wrap gap-2">
            {SEVERITY_OPTIONS.map((option) => {
              const active = value.severity.includes(option);
              return (
                <FilterChip
                  key={option}
                  label={option.toUpperCase()}
                  active={active}
                  onClick={() => onToggleSeverity(option)}
                />
              );
            })}
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Category</p>
          <div className="flex flex-wrap gap-2">
            {categories.length > 0 ? (
              categories.map((option) => {
                const active = value.category.includes(option.name);
                return (
                  <FilterChip
                    key={option.name}
                    label={option.name}
                    count={option.count}
                    active={active}
                    onClick={() => onToggleCategory(option.name)}
                  />
                );
              })
            ) : (
              <span className="text-xs text-slate-500">Categories appear as data loads.</span>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
