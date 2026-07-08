"use client";

import { Check, ExternalLink, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { confirmMatchReview, denyMatchReview, listMatchReviews } from "../../../lib/api";
import type { MatchReview } from "../../../lib/types";

function isHttpUrl(value: string | null | undefined) {
  try {
    const url = new URL(value ?? "");
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function FramePane({ title, url }: { title: string; url: string | null }) {
  const canOpen = isHttpUrl(url);

  return (
    <div className="review-pane">
      <div className="row between">
        <strong>{title}</strong>
        {canOpen && (
          <a className="button" href={url ?? ""} target="_blank" rel="noreferrer">
            <ExternalLink size={16} /> Open
          </a>
        )}
      </div>
      {canOpen ? <iframe src={url ?? ""} title={title} /> : <div className="review-empty muted">Missing URL</div>}
    </div>
  );
}

export default function MatchReviewPage() {
  const queryClient = useQueryClient();
  const [requestedId, setRequestedId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const reviewsQuery = useQuery({ queryKey: ["match-reviews", "pending"], queryFn: () => listMatchReviews("pending") });
  const reviews = reviewsQuery.data ?? [];
  const selected = reviews.find((review) => review.scrape_result_id === selectedId) ?? reviews[0] ?? null;

  useEffect(() => {
    setRequestedId(new URLSearchParams(window.location.search).get("result"));
  }, []);

  useEffect(() => {
    if (requestedId) setSelectedId(requestedId);
  }, [requestedId]);

  useEffect(() => {
    if (!reviews.length) {
      setSelectedId(null);
      return;
    }
    if (!selectedId || !reviews.some((review) => review.scrape_result_id === selectedId)) {
      setSelectedId(reviews[0].scrape_result_id);
    }
  }, [reviews, selectedId]);

  const onSettled = () => {
    queryClient.invalidateQueries({ queryKey: ["match-reviews", "pending"] });
    queryClient.invalidateQueries({ queryKey: ["confirmed-matches"] });
  };
  const confirm = useMutation({
    mutationFn: confirmMatchReview,
    onSuccess: () => {
      setMessage("Confirmed.");
      onSettled();
    },
  });
  const deny = useMutation({
    mutationFn: denyMatchReview,
    onSuccess: () => {
      setMessage("Denied.");
      onSettled();
    },
  });
  const busy = confirm.isPending || deny.isPending;
  const canConfirm = Boolean(selected && isHttpUrl(selected.product_url) && isHttpUrl(selected.competitor_url) && !busy);

  return (
    <main className="page product-workspace">
      <header className="workspace-header">
        <div>
          <h1>Review</h1>
          <p className="muted">Pending LLM matches</p>
        </div>
        <div className="status-pill">{reviews.length} pending</div>
      </header>

      <section className="workspace-grid">
        <div className="panel">
          <h2>Queue</h2>
          {reviewsQuery.isLoading && <p className="muted">Loading matches...</p>}
          {reviewsQuery.error && <p className="error">{reviewsQuery.error.message}</p>}
          {!reviewsQuery.isLoading && !reviews.length && <p className="muted">No pending matches.</p>}
          {!!reviews.length && (
            <div className="result-list">
              {reviews.map((review) => (
                <button
                  key={review.scrape_result_id}
                  className={`result-button${selected?.scrape_result_id === review.scrape_result_id ? " active" : ""}`}
                  onClick={() => {
                    setSelectedId(review.scrape_result_id);
                    setMessage("");
                  }}
                >
                  <strong>{review.sku}</strong>
                  <span>{review.marketplace}</span>
                  <span>{review.match_confidence ?? 0}%</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="panel">
          {selected ? (
            <>
              <div className="row between">
                <div>
                  <h2>{selected.sku}</h2>
                  <p className="muted">{selected.product_title}</p>
                </div>
                <div className="row">
                  <Link className="button" href={`/products/${selected.product_id}`}>
                    Product
                  </Link>
                  <button className="button danger" disabled={!selected || busy} onClick={() => deny.mutate(selected.scrape_result_id)}>
                    <X size={16} /> Deny
                  </button>
                  <button className="button primary" disabled={!canConfirm} onClick={() => confirm.mutate(selected.scrape_result_id)}>
                    <Check size={16} /> Confirm
                  </button>
                </div>
              </div>
              <div className="row">
                <span className="status-pill">{selected.marketplace}</span>
                {selected.price && <span className="status-pill">{selected.price}</span>}
                {selected.match_confidence !== null && <span className="status-pill">{selected.match_confidence}%</span>}
                {selected.matched_at && <span className="muted">{new Date(selected.matched_at).toLocaleString()}</span>}
              </div>
              {selected.match_reason && <p className="muted">{selected.match_reason}</p>}
              {message && <p className="muted">{message}</p>}
              {confirm.error && <p className="error">{confirm.error.message}</p>}
              {deny.error && <p className="error">{deny.error.message}</p>}
              <div className="review-frame-grid">
                <FramePane title="Our URL" url={selected.product_url} />
                <FramePane title="Competitor URL" url={selected.competitor_url} />
              </div>
              <div className="detail-grid">
                <div>
                  <strong>Competitor title</strong>
                  <div className="detail-value">{selected.competitor_title}</div>
                </div>
                <div>
                  <strong>Review status</strong>
                  <div className="detail-value">{selected.review_status}</div>
                </div>
              </div>
            </>
          ) : (
            <p className="muted">Select a match.</p>
          )}
        </div>
      </section>
    </main>
  );
}
