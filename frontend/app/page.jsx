"use client";

import { Suspense } from "react";
import { useCallback, useDeferredValue, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import ControlsBar from "@/components/ControlsBar";
import Navbar from "@/components/Navbar";
import PainPointList from "@/components/PainPointList";
import SkeletonCard from "@/components/SkeletonCard";
import { EmptyState, ErrorState } from "@/components/StateCard";
import { usePainPoints } from "@/hooks/usePainPoints";
import {
  applyDashboardControls,
  collectCategoryOptions,
  parseControlState,
} from "@/lib/dashboardControls";
import { normalizePainPoint } from "@/lib/painPointModel";

const SKELETON_COUNT = 6;

export default function HomePage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <HomePageContent />
    </Suspense>
  );
}

function HomePageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data, loading, error, retry } = usePainPoints();

  const controlState = useMemo(() => parseControlState(searchParams), [searchParams]);
  const deferredSearch = useDeferredValue(controlState.search);

  const items = useMemo(() => (data || []).map(normalizePainPoint), [data]);

  const categoryOptions = useMemo(() => collectCategoryOptions(items), [items]);

  const filteredItems = useMemo(
    () =>
      applyDashboardControls(items, {
        ...controlState,
        search: deferredSearch,
      }),
    [items, controlState, deferredSearch]
  );

  const updateParams = useCallback(
    (patch) => {
      const next = new URLSearchParams(searchParams.toString());
      Object.entries(patch).forEach(([key, value]) => {
        if (value === undefined || value === null || value === "" || (Array.isArray(value) && value.length === 0)) {
          next.delete(key);
          return;
        }

        if (Array.isArray(value)) {
          next.set(key, value.join(","));
          return;
        }

        next.set(key, String(value));
      });

      const query = next.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  const toggleFromArray = useCallback((arrayValue, candidate) => {
    return arrayValue.includes(candidate)
      ? arrayValue.filter((entry) => entry !== candidate)
      : [...arrayValue, candidate];
  }, []);

  const handleClearControls = useCallback(() => {
    router.replace(pathname, { scroll: false });
  }, [pathname, router]);

  return (
    <main className="page-shell">
      <Navbar />

      <section className="mb-6">
        <h1 className="section-title">Pain Point Intelligence Feed</h1>
        <p className="section-caption">
          Structured Reddit signals ranked by score and severity. Designed for fast triage and future search, filter, and sorting layers.
        </p>
      </section>

      <div className="mx-auto w-full lg:w-[96%] xl:w-[94%] 2xl:w-[90%]">
        <ControlsBar
          value={controlState}
          categories={categoryOptions}
          total={items.length}
          filteredTotal={filteredItems.length}
          onSearchChange={(value) => updateParams({ search: value })}
          onSortChange={(sort) => updateParams({ sort })}
          onToggleCategory={(name) =>
            updateParams({
              category: toggleFromArray(controlState.category, name),
            })
          }
          onToggleSeverity={(level) =>
            updateParams({
              severity: toggleFromArray(controlState.severity, level),
            })
          }
          onClear={handleClearControls}
        />

        {loading ? (
          <section className="grid gap-4">
            {Array.from({ length: SKELETON_COUNT }).map((_, index) => (
              <SkeletonCard key={`skeleton-${index}`} />
            ))}
          </section>
        ) : null}

        {!loading && error ? <ErrorState message={error} onRetry={retry} /> : null}

        {!loading && !error && items.length === 0 ? <EmptyState onClear={handleClearControls} hasFilters={false} /> : null}

        {!loading && !error && items.length > 0 && filteredItems.length === 0 ? (
          <EmptyState onClear={handleClearControls} hasFilters />
        ) : null}

        {!loading && !error && filteredItems.length > 0 ? <PainPointList items={filteredItems} /> : null}
      </div>
    </main>
  );
}

function PageSkeleton() {
  return (
    <main className="page-shell">
      <Navbar />
      <section className="mb-6">
        <h1 className="section-title">Pain Point Intelligence Feed</h1>
        <p className="section-caption">Loading dashboard context...</p>
      </section>
      <div className="mx-auto w-full lg:w-[96%] xl:w-[94%] 2xl:w-[90%]">
        <section className="grid gap-4">
          {Array.from({ length: SKELETON_COUNT }).map((_, index) => (
            <SkeletonCard key={`suspense-skeleton-${index}`} />
          ))}
        </section>
      </div>
    </main>
  );
}
