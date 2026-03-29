import { memo } from "react";

const toneClass = {
  neutral: "bg-white/8 text-slate-200 border-white/12",
  accent: "bg-accent-500/15 text-accent-300 border-accent-400/35",
  high: "bg-rose-500/15 text-rose-200 border-rose-400/35",
  medium: "bg-amber-500/15 text-amber-200 border-amber-400/35",
  low: "bg-emerald-500/15 text-emerald-200 border-emerald-400/35",
};

function Badge({ children, tone = "neutral" }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold tracking-wide ${toneClass[tone] || toneClass.neutral}`}
    >
      {children}
    </span>
  );
}

export default memo(Badge);
