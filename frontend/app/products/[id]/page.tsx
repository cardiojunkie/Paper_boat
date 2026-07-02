"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { getProduct, getProductScrapeResults, scrapeMarkdownUrl } from "../../../lib/api";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const [search, setSearch] = useState("");
  const query = useQuery({ queryKey: ["product", params.id], queryFn: () => getProduct(params.id) });
  const scrapeResults = useQuery({ queryKey: ["product-scrape-results", params.id], queryFn: () => getProductScrapeResults(params.id) });
  const product = query.data;
  const attributes = useMemo(() => {
    const entries = Object.entries(product?.attributes ?? {});
    const term = search.toLowerCase();
    return term ? entries.filter(([key, value]) => `${key} ${String(value)}`.toLowerCase().includes(term)) : entries;
  }, [product, search]);

  return (
    <main className="page">
      {query.isLoading && <div className="panel muted">Loading product...</div>}
      {query.error && <div className="panel error">{query.error.message}</div>}
      {product && (
        <div className="grid">
          <div>
            <h1>{product.sku}</h1>
            <p className="muted">{product.title}</p>
          </div>
          <div className="panel detail-grid">
            {["product_type", "attribute_set", "category", "l1", "l2", "l3", "l4", "search_query", "source_filename", "created_at", "updated_at"].map((field) => (
              <div key={field}>
                <strong>{field.replaceAll("_", " ")}</strong>
                <div>{String(product[field as keyof typeof product] ?? "")}</div>
              </div>
            ))}
          </div>
          <div className="panel">
            <h2>Scrape results</h2>
            {scrapeResults.isLoading && <p className="muted">Loading scrape results...</p>}
            {scrapeResults.error && <p className="error">{scrapeResults.error.message}</p>}
            {!scrapeResults.isLoading && !scrapeResults.data?.length && <p className="muted">No scrape results yet.</p>}
            {!!scrapeResults.data?.length && (
              <table>
                <thead>
                  <tr>
                    <th>Marketplace</th>
                    <th>Status</th>
                    <th>Results</th>
                    <th>Search URL</th>
                    <th>Markdown</th>
                  </tr>
                </thead>
                <tbody>
                  {scrapeResults.data.map((result) => (
                    <tr key={result.id}>
                      <td>{result.marketplace}</td>
                      <td>{result.status}</td>
                      <td>{result.result_count}</td>
                      <td>
                        <a href={result.search_url} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      </td>
                      <td>
                        <a href={scrapeMarkdownUrl(result.id)} target="_blank" rel="noreferrer">
                          Markdown
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <div className="panel">
            <div className="row">
              <h2>Dynamic attributes</h2>
              <input className="input" placeholder="Search attributes" value={search} onChange={(event) => setSearch(event.target.value)} />
            </div>
            <table>
              <tbody>
                {attributes.map(([key, value]) => (
                  <tr key={key}>
                    <th>{key}</th>
                    <td>{value == null ? "" : String(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="panel">
            <h2>Source row</h2>
            <pre>{JSON.stringify(product.source_row, null, 2)}</pre>
          </div>
        </div>
      )}
    </main>
  );
}
