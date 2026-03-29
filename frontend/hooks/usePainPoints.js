"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchPainPoints } from "@/lib/api";

export function usePainPoints() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const abortRef = useRef(null);

  const loadPainPoints = useCallback(async () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }

    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError("");

    try {
      const nextData = await fetchPainPoints(controller.signal);
      setData(nextData);
    } catch (err) {
      if (err.name !== "AbortError") {
        setError(err.message || "Something went wrong while loading data.");
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadPainPoints();

    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, [loadPainPoints]);

  return {
    data,
    loading,
    error,
    retry: loadPainPoints,
  };
}
