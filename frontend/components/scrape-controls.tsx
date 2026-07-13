"use client";

import { Search } from "lucide-react";
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { createScrapeJob, getMarketplaces, getScrapeJob } from "../lib/api";
import type { Marketplace } from "../lib/types";

const terminal = new Set(["completed", "completed_with_errors", "failed"]);

export function ScrapeControls({ selectedIds, onStaleSelection }: { selectedIds: string[]; onStaleSelection: () => void }) {
  const queryClient = useQueryClient();
  const [selectedMarketplaces, setSelectedMarketplaces] = useState<Marketplace["key"][]>([]);
  const [jobIds, setJobIds] = useState<string[]>([]);
  const marketplaces = useQuery({ queryKey: ["marketplaces"], queryFn: getMarketplaces });
  const createJob = useMutation({
    mutationFn: () => createScrapeJob(selectedIds, selectedMarketplaces),
    onSuccess: (data) => setJobIds(data.jobs.map((job) => job.job_id)),
    onError: (error) => {
      if (error instanceof Error && error.message.includes("Products not found")) {
        setJobIds([]);
        onStaleSelection();
        queryClient.invalidateQueries({ queryKey: ["products"] });
      }
    },
  });
  const jobs = useQueries({
    queries: jobIds.map((jobId) => ({
      queryKey: ["scrape-job", jobId],
      queryFn: () => getScrapeJob(jobId),
      refetchInterval: (query: { state: { data?: { status?: string } } }) => {
        const status = query.state.data?.status;
        return status && terminal.has(status) ? false : 1500;
      },
    })),
  });
  const jobData = jobs.map((job) => job.data).filter(Boolean);
  const completed = jobData.filter((job) => job && terminal.has(job.status)).length;
  const failed = jobData.filter((job) => job?.status === "failed" || job?.status === "completed_with_errors").length;
  const jobError = jobs.find((job) => job.error)?.error;

  return (
    <div className="scrape-controls">
      <div className="marketplace-group">
        {(marketplaces.data ?? []).map((marketplace) => (
          <label key={marketplace.key} className="marketplace-option">
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
          <Search size={16} /> Scrape
        </button>
      </div>
      {marketplaces.error && <p className="error">{marketplaces.error.message}</p>}
      {createJob.error && <p className="error">{createJob.error.message}</p>}
      {jobIds.length > 0 && (
        <p className="muted action-message" aria-live="polite">
          SKU jobs: {completed} done, {failed} with errors, {jobIds.length} total.
        </p>
      )}
      {jobError && <p className="error">{jobError.message}</p>}
    </div>
  );
}
