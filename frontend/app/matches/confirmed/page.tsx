"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, ExternalLink, RefreshCw } from "lucide-react";
import Link from "next/link";

import { listConfirmedMatches } from "../../../lib/api";

export default function ConfirmedMatchesPage() {
  const query = useQuery({ queryKey: ["confirmed-matches"], queryFn: listConfirmedMatches });
  const matches = query.data ?? [];

  return (
    <main className="page confirmed-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">Marketplace sync</span>
          <h1>Confirmed Matches History</h1>
          <p>Review established competitor links and their latest recorded prices.</p>
        </div>
        <div className="confirmed-summary">
          <CheckCircle2 size={18} />
          <strong>{matches.length.toLocaleString()}</strong>
          <span>confirmed</span>
        </div>
      </header>

      {query.isLoading && <div className="panel empty-state muted">Loading matches...</div>}
      {query.error && <div className="panel empty-state error">{query.error.message}</div>}
      {!query.isLoading && !matches.length && <div className="panel empty-state muted">No confirmed matches.</div>}
      {!!matches.length && (
        <section className="history-panel">
          <div className="history-toolbar">
            <div className="row">
              <RefreshCw size={16} />
              <strong>Synced marketplace records</strong>
            </div>
            <span className="muted">All confirmed matches</span>
          </div>
          <div className="table-wrap" tabIndex={0} aria-label="Confirmed matches table">
            <table className="confirmed-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Marketplace</th>
                  <th>Our title</th>
                  <th>Competitor title</th>
                  <th>Competitor price</th>
                  <th>Confirmed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((match) => (
                  <tr key={match.id}>
                    <td>
                      <Link className="sku-link" href={`/products/${match.product_id}`}>{match.sku}</Link>
                    </td>
                    <td><span className="market-badge">{match.marketplace}</span></td>
                    <td>{match.product_title ?? "—"}</td>
                    <td>{match.competitor_title}</td>
                    <td className="price-cell">{match.price ?? "—"}</td>
                    <td>{new Date(match.confirmed_at).toLocaleDateString()}</td>
                    <td>
                      <div className="row table-actions">
                        <a className="external-icon" aria-label="Open our product listing" href={match.product_url} target="_blank" rel="noreferrer">
                          <ExternalLink size={15} />
                        </a>
                        <a className="external-icon" aria-label="Open competitor listing" href={match.competitor_url} target="_blank" rel="noreferrer">
                          <ExternalLink size={15} />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <footer className="history-footer">
            Showing {matches.length.toLocaleString()} confirmed {matches.length === 1 ? "match" : "matches"}
          </footer>
        </section>
      )}
    </main>
  );
}
