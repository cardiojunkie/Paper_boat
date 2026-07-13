"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, Check, Database, ExternalLink, Link2Off, Search, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { confirmMatchReview, denyMatchReview, listMatchReviews } from "../../../lib/api";

function isHttpUrl(value: string | null | undefined) {
  try {
    const url = new URL(value ?? "");
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function ComparisonCard({
  kind,
  title,
  url,
  rows,
}: {
  kind: "catalog" | "competitor";
  title: string;
  url: string | null;
  rows: [string, string | null | undefined][];
}) {
  const canOpen = isHttpUrl(url);

  return (
    <article className="comparison-card">
      <header>
        <span>{kind === "catalog" ? <Database size={17} /> : <Search size={17} />}{title}</span>
        {canOpen && (
          <a className="external-icon" aria-label={`Open ${title}`} href={url ?? ""} target="_blank" rel="noreferrer">
            <ExternalLink size={16} />
          </a>
        )}
      </header>
      <div className={`comparison-placeholder ${kind}`}>
        {kind === "catalog" ? <Database size={34} /> : <Search size={34} />}
        <span>{kind === "catalog" ? "Internal product record" : "Scraped marketplace result"}</span>
      </div>
      <dl>
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value || "—"}</dd>
          </div>
        ))}
        <div>
          <dt>URL</dt>
          <dd>
            {canOpen ? (
              <a className="row-link" href={url ?? ""} target="_blank" rel="noreferrer">
                Open listing <ExternalLink size={13} />
              </a>
            ) : (
              <span className="error">Missing or invalid</span>
            )}
          </dd>
        </div>
      </dl>
    </article>
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
      setMessage("Match confirmed.");
      onSettled();
    },
  });
  const deny = useMutation({
    mutationFn: denyMatchReview,
    onSuccess: () => {
      setMessage("Match denied.");
      onSettled();
    },
  });
  const busy = confirm.isPending || deny.isPending;
  const productUrlValid = isHttpUrl(selected?.product_url);
  const competitorUrlValid = isHttpUrl(selected?.competitor_url);
  const canConfirm = Boolean(selected && productUrlValid && competitorUrlValid && !busy);

  return (
    <main className="review-page">
      <section className="review-workspace">
        <aside className="review-queue">
          <header>
            <span>Review queue</span>
            <strong>{reviews.length}</strong>
          </header>
          {reviewsQuery.isLoading && <p className="muted queue-state">Loading matches...</p>}
          {reviewsQuery.error && <p className="error queue-state">{reviewsQuery.error.message}</p>}
          {!reviewsQuery.isLoading && !reviews.length && <p className="muted queue-state">No pending matches.</p>}
          {!!reviews.length && (
            <div className="queue-list">
              {reviews.map((review) => (
                <button
                  key={review.scrape_result_id}
                  className={selected?.scrape_result_id === review.scrape_result_id ? "active" : ""}
                  aria-pressed={selected?.scrape_result_id === review.scrape_result_id}
                  onClick={() => {
                    setSelectedId(review.scrape_result_id);
                    setMessage("");
                  }}
                >
                  <span className="queue-item-top">
                    <strong>{review.sku}</strong>
                    <span>{review.match_confidence ?? 0}% match</span>
                  </span>
                  <span className="queue-title">{review.product_title || "Untitled product"}</span>
                  <small>{review.marketplace}</small>
                </button>
              ))}
            </div>
          )}
        </aside>

        <section className="review-canvas">
          {selected ? (
            <>
              <header className="review-header">
                <div>
                  <div className="row">
                    <h1>{selected.sku}</h1>
                    <span className="market-badge">{selected.marketplace}</span>
                  </div>
                  <p>{selected.product_title}</p>
                </div>
                {selected.price && (
                  <div className="review-price">
                    <strong>{selected.price}</strong>
                    <span>Competitor price</span>
                  </div>
                )}
              </header>

              <div className="match-analysis-banner">
                <Bot size={23} />
                <div>
                  <strong>LLM Match Analysis: {selected.match_confidence ?? 0}% Confidence</strong>
                  <p>{selected.match_reason || "No match reasoning was returned."}</p>
                </div>
              </div>

              {(!productUrlValid || !competitorUrlValid) && (
                <div className="url-warning" role="alert">
                  <Link2Off size={24} />
                  <div>
                    <strong>Missing source URL</strong>
                    <p>A valid URL is required for both records before this match can be confirmed.</p>
                  </div>
                </div>
              )}

              <div className="comparison-grid">
                <ComparisonCard
                  kind="catalog"
                  title="Internal catalog (source)"
                  url={selected.product_url}
                  rows={[
                    ["SKU", selected.sku],
                    ["Title", selected.product_title],
                    ["Status", selected.review_status],
                  ]}
                />
                <ComparisonCard
                  kind="competitor"
                  title="Scraped competitor data"
                  url={selected.competitor_url}
                  rows={[
                    ["Marketplace", selected.marketplace],
                    ["Title", selected.competitor_title],
                    ["Price", selected.price],
                  ]}
                />
              </div>

              {(message || confirm.error || deny.error) && (
                <div className="review-message" aria-live="polite">
                  {message && <span>{message}</span>}
                  {confirm.error && <span className="error">{confirm.error.message}</span>}
                  {deny.error && <span className="error">{deny.error.message}</span>}
                </div>
              )}

              <footer className="review-actions">
                <Link className="button" href={`/products/${selected.product_id}`}>
                  View product
                </Link>
                <div className="row">
                  <button className="button danger solid" disabled={busy} onClick={() => deny.mutate(selected.scrape_result_id)}>
                    <X size={16} /> Deny match
                  </button>
                  <button className="button primary" disabled={!canConfirm} onClick={() => confirm.mutate(selected.scrape_result_id)}>
                    <Check size={16} /> Confirm match
                  </button>
                </div>
              </footer>
            </>
          ) : (
            <div className="review-empty-state">
              <Check size={30} />
              <h1>Queue clear</h1>
              <p className="muted">There are no pending matches to review.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
