import { memo } from "react";

function normalizeScore(score) {
  if (typeof score !== "number" || Number.isNaN(score)) return 0;
  const scaled = score <= 1 ? score * 100 : score;
  return Math.max(0, Math.min(100, scaled));
}

function formatDate(isoDate) {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return "Unknown date";

  return new Intl.DateTimeFormat("en-US", {
    month: "numeric",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function buildSolutionName(item) {
  const category = String(item.category || "").trim();
  if (!category) return "AI Opportunity Pilot";
  return `${category} AutoPilot`;
}

function buildSummary(item) {
  if (item.summary) return item.summary;
  return "A SaaS workflow that turns this repeated pain signal into an actionable product opportunity with automation and clear user value.";
}

function PainPointCard({ item }) {
  const score = normalizeScore(item.score);
  const scoreLabel = `${score.toFixed(0)}/100`;
  const userHandle = item.reddit_id ? `u/${item.reddit_id}` : "u/anonymous";
  const solutionName = buildSolutionName(item);
  const insightSummary = buildSummary(item);
  const complexity = String(item.severity || "medium").toLowerCase();
  const cardHeadline =
    (item.pain_point_headline && String(item.pain_point_headline).trim()) ||
    (item.pain_point && String(item.pain_point).trim()) ||
    item.post_title ||
    "Untitled Pain Point";

  return (
    <article className="group overflow-hidden rounded-[1.35rem] border border-[#2e2417] bg-[#13100e] shadow-[0_0_0_1px_rgba(255,176,76,0.06),0_22px_42px_rgba(0,0,0,0.42)] transition-colors duration-200 hover:border-[#5a3b1b] [contain-intrinsic-size:510px] [content-visibility:auto]">
      <div className="px-5 pb-4 pt-4 sm:px-7">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full border border-[#5c3f14] bg-[#1d1710] px-3 py-1 text-xs font-semibold text-[#d88d1b]">
              {item.subreddit || "r/unknown"}
            </span>
            <span className="inline-flex items-center rounded-full bg-[#3b82f6] px-3 py-1 text-xs font-semibold text-white">
              {item.category || "General"}
            </span>
          </div>

          <span className="inline-flex items-center rounded-full border border-[#4c1d1d] bg-[#261111] px-3 py-1 text-xs font-bold leading-none text-[#ff3131] sm:text-sm">
            {scoreLabel}
          </span>
        </div>

        <h3 className="mb-3 line-clamp-2 text-[1.05rem] font-extrabold leading-tight text-white sm:text-[1.45rem]">
          {cardHeadline}
        </h3>

        <div className="mb-3 flex items-center gap-3">
          <div className="h-[6px] flex-1 overflow-hidden rounded-full bg-[#272727]">
            <div className="h-full rounded-full bg-[#ff2f43]" style={{ width: `${score}%` }} />
          </div>
          <span className="text-xs font-bold text-white sm:text-sm">{scoreLabel}</span>
        </div>
      </div>

      <div className="h-px bg-[#2a231c]" />

      <div className="grid md:grid-cols-2">
        <section className="px-5 py-4 sm:px-7">
          <p className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-[#a79b8a] sm:text-xs">
            REDDIT EVIDENCE <span className="text-[#ffb000]">- 1 POST</span>
          </p>

          <div className="rounded-2xl border border-[#25211d] bg-[#181513] p-4">
            <p className="mb-3 line-clamp-3 text-xs italic leading-relaxed text-[#d2c6b5] sm:text-sm">
              "{item.pain_point || "No pain point description provided."}"
            </p>

            <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] sm:text-xs">
              <span className="text-[#aca290]">
                {userHandle} <span className="mx-1 text-[#7f7466]">-</span> <span className="text-[#f2a63a]">{formatDate(item.created_at)}</span>
              </span>

              <div className="flex items-center gap-4">
                <span className="text-[#bbb09f]">Message</span>
                <a
                  className="font-semibold text-[#ffb000] transition-colors hover:text-[#ffc44a]"
                  href={item.post_url || "#"}
                  target="_blank"
                  rel="noreferrer"
                >
                  View on Reddit
                </a>
              </div>
            </div>
          </div>
        </section>

        <section className="border-t border-[#2a231c] px-5 py-4 md:border-l md:border-t-0 sm:px-7">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#a79b8a] sm:text-xs">AI SOLUTION IDEA</p>

          <div className="rounded-2xl border border-[#65481d] bg-[#2a1f12] p-4">
            <h4 className="mb-2 line-clamp-2 text-sm font-extrabold text-white sm:text-base">{solutionName}</h4>
            <p className="mb-3 line-clamp-2 text-xs leading-relaxed text-[#d0c1aa] sm:text-sm">{insightSummary}</p>

            <div className="space-y-1 border-t border-[#4b3923] pt-3 text-[11px] sm:text-xs">
              <p>
                <span className="font-semibold text-white">Target:</span>{" "}
                <span className="text-[#d0c1aa]">Operators, founders, and PM-led teams</span>
              </p>
              <p>
                <span className="font-semibold text-white">Monetization:</span>{" "}
                <span className="text-[#d0c1aa]">Subscription with usage-based expansion</span>
              </p>
              <p>
                <span className="font-semibold text-white">Complexity:</span>{" "}
                <span className="inline-flex rounded-full border border-[#725735] bg-[#3b2f1f] px-2 py-0.5 text-xs font-semibold uppercase text-[#f0d8ab]">
                  {complexity}
                </span>
              </p>
            </div>
          </div>
        </section>
      </div>
    </article>
  );
}

export default memo(PainPointCard);
