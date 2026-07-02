"use client";

import { Search } from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { createScrapeJob, getMarketplaces, getScrapeJob } from "../lib/api";
import type { Marketplace } from "../lib/types";

const terminal = new Set(["completed", "completed_with_errors", "failed"]);

export function ScrapeControls({ selectedIds }: { selectedIds: string[] }) {
  const [selectedMarketplaces, setSelectedMarketplaces] = useState<Marketplace["key"][]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const marketplaces = useQuery({ queryKey: ["marketplaces"], queryFn: getMarketplaces });
  const createJob = useMutation({
    mutationFn: () => createScrapeJob(selectedIds, selectedMarketplaces),
    onSuccess: (data) => setJobId(data.job_id),
  });
  const job = useQuery({
    queryKey: ["scrape-job", jobId],
    queryFn: () => getScrapeJob(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && terminal.has(status) ? false : 1500;
    },
  });

  return (
    <div className="panel">
      <div className="row">
        <span className="muted">Scrape selected products: {selectedIds.length}</span>
        {(marketplaces.data ?? []).map((marketplace) => (
          <label key={marketplace.key} className="button">
            <input
              type="checkbox"
              checked={selectedMarketplaces.includes(marketplace.key)}
              onChange={(event) => {
                setSelectedMarketplaces((current) =>
                  event.target.checked ? [...current, marketplace.key] : current.filter((key) => key !== marketplace.key),
                );
              }}
            />
            {marketplace.label}
          </label>
        ))}
        <button
          className="button primary"
          disabled={!selectedIds.length || !selectedMarketplaces.length || createJob.isPending}
          onClick={() => createJob.mutate()}
        >
          <Search size={16} /> Scrape selected
        </button>
      </div>
      {marketplaces.error && <p className="error">{marketplaces.error.message}</p>}
      {createJob.error && <p className="error">{createJob.error.message}</p>}
      {job.data && (
        <p className="muted">
          Job {job.data.status}: {job.data.completed_targets} completed, {job.data.failed_targets} failed, {job.data.total_targets} total.
        </p>
      )}
      {job.error && <p className="error">{job.error.message}</p>}
    </div>
  );
}
