"use client";

import { ExternalLink } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { listConfirmedMatches } from "../../../lib/api";

export default function ConfirmedMatchesPage() {
  const query = useQuery({ queryKey: ["confirmed-matches"], queryFn: listConfirmedMatches });
  const matches = query.data ?? [];

  return (
    <main className="page product-workspace">
      <header className="workspace-header">
        <div>
          <h1>Confirmed</h1>
          <p className="muted">Exact matches</p>
        </div>
        <div className="status-pill">{matches.length} matches</div>
      </header>

      {query.isLoading && <div className="panel muted">Loading matches...</div>}
      {query.error && <div className="panel error">{query.error.message}</div>}
      {!query.isLoading && !matches.length && <div className="panel muted">No confirmed matches.</div>}
      {!!matches.length && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Marketplace</th>
                <th>Product title</th>
                <th>Our URL</th>
                <th>Competitor title</th>
                <th>Competitor URL</th>
                <th>Price</th>
                <th>Confirmed</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((match) => (
                <tr key={match.id}>
                  <td>
                    <Link href={`/products/${match.product_id}`}>{match.sku}</Link>
                  </td>
                  <td>{match.marketplace}</td>
                  <td>{match.product_title ?? ""}</td>
                  <td>
                    <a className="url row-link" href={match.product_url} target="_blank" rel="noreferrer">
                      <ExternalLink size={14} /> {match.product_url}
                    </a>
                  </td>
                  <td>{match.competitor_title}</td>
                  <td>
                    <a className="url row-link" href={match.competitor_url} target="_blank" rel="noreferrer">
                      <ExternalLink size={14} /> {match.competitor_url}
                    </a>
                  </td>
                  <td>{match.price ?? ""}</td>
                  <td>{new Date(match.confirmed_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
