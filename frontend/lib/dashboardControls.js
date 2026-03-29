export const SORT_OPTIONS = {
  latest: "latest",
  highest_score: "highest_score",
};

export const SEVERITY_OPTIONS = ["high", "medium", "low"];

export function parseControlState(searchParams) {
  const search = searchParams.get("search") || "";
  const category = splitCsv(searchParams.get("category"));
  const severity = splitCsv(searchParams.get("severity"));
  const sortParam = searchParams.get("sort");
  const sort = Object.values(SORT_OPTIONS).includes(sortParam) ? sortParam : SORT_OPTIONS.latest;

  return {
    search,
    category,
    severity,
    sort,
  };
}

export function applyDashboardControls(items, controls) {
  const query = controls.search.trim().toLowerCase();

  const filtered = items.filter((item) => {
    const matchesSearch =
      !query ||
      [item.pain_point_headline, item.post_title, item.pain_point, item.subreddit, item.category]
        .filter(Boolean)
        .some((field) => String(field).toLowerCase().includes(query));

    const matchesCategory =
      controls.category.length === 0 || controls.category.includes(String(item.category || ""));

    const matchesSeverity =
      controls.severity.length === 0 ||
      controls.severity.includes(String(item.severity || "").toLowerCase());

    return matchesSearch && matchesCategory && matchesSeverity;
  });

  if (controls.sort === SORT_OPTIONS.highest_score) {
    return [...filtered].sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0));
  }

  return [...filtered].sort((a, b) => {
    const aTime = Date.parse(a.created_at || 0);
    const bTime = Date.parse(b.created_at || 0);
    return bTime - aTime;
  });
}

export function collectCategoryOptions(items) {
  const tally = new Map();

  for (const item of items) {
    const key = item.category || "Uncategorized";
    tally.set(key, (tally.get(key) || 0) + 1);
  }

  return [...tally.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, count]) => ({ name, count }));
}

function splitCsv(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}
