export function normalizePainPoint(raw = {}) {
  return {
    id: raw.id ?? null,
    reddit_id: raw.reddit_id ?? "",
    subreddit: raw.subreddit ?? "r/unknown",
    post_title: raw.post_title ?? "Untitled post",
    pain_point_headline: raw.pain_point_headline ?? "",
    post_url: raw.post_url ?? "#",
    pain_point: raw.pain_point ?? "No pain point description provided.",
    category: raw.category ?? "Uncategorized",
    severity: raw.severity ?? "unknown",
    score: raw.score ?? 0,
    created_at: raw.created_at ?? null,
    summary: raw.summary ?? "",
    solution_placeholder: raw.solution_placeholder ?? "",
    extra_insight: raw.extra_insight ?? "",
  };
}
