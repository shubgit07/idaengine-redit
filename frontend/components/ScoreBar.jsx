import { memo } from "react";

function normalizeScore(score) {
  if (typeof score !== "number" || Number.isNaN(score)) return 0;

  const normalized = score <= 1 ? score * 100 : score;
  return Math.max(0, Math.min(100, normalized));
}

function ScoreBar({ score }) {
  const value = normalizeScore(score);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="font-medium uppercase tracking-widest">Signal Score</span>
        <span className="text-slate-200">{value.toFixed(0)}%</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-600 via-accent-500 to-accent-300 shadow-[0_0_18px_rgba(249,148,74,0.45)] transition-[width] duration-300 ease-out"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export default memo(ScoreBar);
