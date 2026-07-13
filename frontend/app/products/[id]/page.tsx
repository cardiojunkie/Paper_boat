"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Bot, Database, ExternalLink, FileText, RotateCcw, Save, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  getProduct,
  getProductScrapeResults,
  getScrapeMarkdown,
  runScrapeMatch,
  scrapeMarkdownUrl,
  updateScrapeMarkdown,
} from "../../../lib/api";
import type { ScrapeResult } from "../../../lib/types";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [attributeSearch, setAttributeSearch] = useState("");
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [message, setMessage] = useState("");
  const query = useQuery({ queryKey: ["product", params.id], queryFn: () => getProduct(params.id) });
  const scrapeResults = useQuery({ queryKey: ["product-scrape-results", params.id], queryFn: () => getProductScrapeResults(params.id) });
  const product = query.data;
  const results = scrapeResults.data ?? [];
  const selectedResult = useMemo(
    () => results.find((result) => result.id === selectedResultId) ?? results[0] ?? null,
    [results, selectedResultId],
  );
  const markdown = useQuery({
    queryKey: ["scrape-markdown", selectedResult?.id ?? ""],
    queryFn: () => getScrapeMarkdown(selectedResult?.id ?? ""),
    enabled: Boolean(selectedResult?.markdown_path),
  });
  const saveMarkdown = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) => updateScrapeMarkdown(id, content),
    onSuccess: (data, variables) => {
      queryClient.setQueryData(["scrape-markdown", variables.id], data.content);
      setMessage("Markdown saved.");
    },
  });
  const runMatch = useMutation({
    mutationFn: runScrapeMatch,
    onSuccess: (updated) => {
      queryClient.setQueryData(["product-scrape-results", params.id], (current?: ScrapeResult[]) =>
        current?.map((result) => (result.id === updated.id ? updated : result)),
      );
    },
  });
  const attributes = useMemo(() => {
    const entries = Object.entries(product?.attributes ?? {});
    const term = attributeSearch.toLowerCase();
    return term ? entries.filter(([key, value]) => `${key} ${String(value)}`.toLowerCase().includes(term)) : entries;
  }, [product, attributeSearch]);

  useEffect(() => {
    setDraft(markdown.data ?? "");
    setMessage("");
  }, [markdown.data, selectedResult?.id]);

  const detailFields: [string, string | null][] = product
    ? [
        ["Product type", product.product_type],
        ["Attribute set", product.attribute_set],
        ["Category", product.category],
        ["L1", product.l1],
        ["L2", product.l2],
        ["L3", product.l3],
        ["L4", product.l4],
        ["Search query", product.search_query],
        ["Source file", product.source_filename],
        ["Created", new Date(product.created_at).toLocaleString()],
        ["Updated", new Date(product.updated_at).toLocaleString()],
      ]
    : [];
  const canSave = Boolean(selectedResult?.markdown_path) && !markdown.isLoading && draft !== (markdown.data ?? "");

  return (
    <main className="page detail-page">
      {query.isLoading && <div className="empty-state muted">Loading product...</div>}
      {query.error && <div className="empty-state error">{query.error.message}</div>}
      {product && (
        <>
          <header className="detail-topbar">
            <div className="detail-heading">
              <Link className="icon-button back-button" aria-label="Back to products" href="/products">
                <ArrowLeft size={19} />
              </Link>
              <div>
                <div className="row detail-kicker">
                  <span className="sku-badge">SKU: {product.sku}</span>
                  <span className="status-pill">{results.length} scrape results</span>
                </div>
                <h1>{product.title || product.sku}</h1>
              </div>
            </div>
            {product.product_url && (
              <a className="button" href={product.product_url} target="_blank" rel="noreferrer">
                <ExternalLink size={16} /> View source
              </a>
            )}
          </header>

          <div className="detail-content">
            <section className="detail-overview">
              <article className="panel metadata-card">
                <div className="panel-heading">
                  <Database size={17} />
                  <h2>Core metadata</h2>
                </div>
                <div className="metadata-grid">
                  {detailFields.map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <strong>{String(value ?? "—")}</strong>
                    </div>
                  ))}
                </div>
                {(product.bullet_points || product.specs) && (
                  <div className="metadata-description">
                    {product.bullet_points && <p>{product.bullet_points}</p>}
                    {product.specs && <p>{product.specs}</p>}
                  </div>
                )}
              </article>

              <article className="panel sources-card">
                <div className="panel-heading">
                  <Search size={17} />
                  <h2>Sources</h2>
                </div>
                {scrapeResults.isLoading && <p className="muted">Loading scrape results...</p>}
                {scrapeResults.error && <p className="error">{scrapeResults.error.message}</p>}
                {!scrapeResults.isLoading && !results.length && <p className="muted">No scrape results yet.</p>}
                {!!results.length && (
                  <div className="source-list">
                    {results.map((result) => (
                      <button
                        key={result.id}
                        className={`source-button${selectedResult?.id === result.id ? " active" : ""}`}
                        onClick={() => setSelectedResultId(result.id)}
                      >
                        <span className="source-name">{result.marketplace}</span>
                        <span className={`status-label status-${result.status}`}>{result.status.replaceAll("_", " ")}</span>
                        <small>{result.result_count} listings</small>
                      </button>
                    ))}
                  </div>
                )}
              </article>

              <article className="panel ai-card">
                <div className="ai-card-header">
                  <div className="panel-heading">
                    <Bot size={20} />
                    <h2>AI Match Analysis</h2>
                  </div>
                  {selectedResult?.match_confidence !== null && selectedResult?.match_confidence !== undefined && (
                    <strong className="confidence-score">{selectedResult.match_confidence}%</strong>
                  )}
                </div>
                {selectedResult ? (
                  <>
                    <div className="row match-meta">
                      <span className={`status-label status-${selectedResult.match_status}`}>{selectedResult.match_status.replaceAll("_", " ")}</span>
                      <span className="status-label">{selectedResult.review_status}</span>
                      {selectedResult.match_model && <span className="muted">Model: {selectedResult.match_model}</span>}
                    </div>
                    <div className="reasoning-block">
                      <span>Reasoning</span>
                      <p>{selectedResult.match_reason || "Run matching to generate an analysis for this source."}</p>
                    </div>
                    {selectedResult.match_error_message && <p className="error">{selectedResult.match_error_message}</p>}
                    {runMatch.error && <p className="error">{runMatch.error.message}</p>}
                    <div className="row ai-actions">
                      {selectedResult.match_status === "matched" && selectedResult.matched_item_id && (
                        <Link className="button" href={`/matches/review?result=${selectedResult.id}`}>
                          <ExternalLink size={16} /> Review match
                        </Link>
                      )}
                      <button
                        className="button primary"
                        disabled={!selectedResult.items.length || selectedResult.match_status === "running" || runMatch.isPending}
                        onClick={() => runMatch.mutate(selectedResult.id)}
                      >
                        <Sparkles size={16} /> {selectedResult.match_status === "matched" ? "Rerun match" : "Run match"}
                      </button>
                    </div>
                  </>
                ) : (
                  <p className="muted">Select a completed source to inspect its match analysis.</p>
                )}
              </article>
            </section>

            {selectedResult && (
              <>
                <section className="panel cross-reference">
                  <div className="panel-heading panel-heading-between">
                    <div className="row">
                      <Search size={17} />
                      <h2>Data cross-reference</h2>
                    </div>
                    <span className={`status-label status-${selectedResult.status}`}>{selectedResult.status.replaceAll("_", " ")}</span>
                  </div>
                  <div className="source-url-row">
                    <span className="muted">Search URL</span>
                    <a href={selectedResult.search_url} target="_blank" rel="noreferrer">
                      {selectedResult.search_url} <ExternalLink size={13} />
                    </a>
                  </div>
                  {selectedResult.error_message && <p className="error">{selectedResult.error_message}</p>}
                  {!!selectedResult.items.length ? (
                    <div className="table-wrap" tabIndex={0} aria-label={`${selectedResult.marketplace} scraped listings`}>
                      <table className="compact-table">
                        <thead>
                          <tr>
                            <th>Match</th>
                            <th>Source</th>
                            <th>Extracted title</th>
                            <th>Price</th>
                            <th>URL</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedResult.items.map((item) => (
                            <tr key={item.id} className={item.id === selectedResult.matched_item_id ? "matched-row" : undefined}>
                              <td><span className={`match-radio${item.id === selectedResult.matched_item_id ? " selected" : ""}`} /></td>
                              <td>{selectedResult.marketplace}</td>
                              <td>{item.title}</td>
                              <td>{item.price ?? "—"}</td>
                              <td>
                                <a className="row-link" href={item.url} target="_blank" rel="noreferrer">
                                  Open <ExternalLink size={13} />
                                </a>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="muted">No extracted listings for this source.</p>
                  )}
                </section>

                <section className="panel markdown-panel">
                  <div className="panel-heading panel-heading-between">
                    <div className="row">
                      <FileText size={17} />
                      <h2>Normalized description (Markdown)</h2>
                    </div>
                    <div className="row">
                      {selectedResult.markdown_path && (
                        <a className="button" href={scrapeMarkdownUrl(selectedResult.id)} target="_blank" rel="noreferrer">
                          <ExternalLink size={15} /> Raw
                        </a>
                      )}
                      <button className="button" disabled={!selectedResult.markdown_path || markdown.isLoading} onClick={() => setDraft(markdown.data ?? "")}>
                        <RotateCcw size={15} /> Reset
                      </button>
                      <button
                        className="button primary"
                        disabled={!canSave || saveMarkdown.isPending}
                        onClick={() => saveMarkdown.mutate({ id: selectedResult.id, content: draft })}
                      >
                        <Save size={15} /> Save changes
                      </button>
                    </div>
                  </div>
                  {markdown.isLoading && <p className="muted">Loading markdown...</p>}
                  {markdown.error && <p className="error">{markdown.error.message}</p>}
                  {saveMarkdown.error && <p className="error">{saveMarkdown.error.message}</p>}
                  {message && <p className="muted" aria-live="polite">{message}</p>}
                  {!selectedResult.markdown_path && <p className="muted">Markdown has not been generated.</p>}
                  {selectedResult.markdown_path && (
                    <textarea
                      className="input markdown-editor"
                      aria-label="Normalized product description in Markdown"
                      value={draft}
                      onChange={(event) => {
                        setDraft(event.target.value);
                        setMessage("");
                      }}
                    />
                  )}
                </section>
              </>
            )}

            <section className="detail-bottom-grid">
              <article className="panel attributes-panel">
                <div className="panel-heading panel-heading-between">
                  <h2>Dynamic attributes</h2>
                  <label className="search-field compact-search">
                    <Search size={15} />
                    <span className="sr-only">Search attributes</span>
                    <input value={attributeSearch} placeholder="Search attributes" onChange={(event) => setAttributeSearch(event.target.value)} />
                  </label>
                </div>
                {!!attributes.length ? (
                  <div className="table-wrap" tabIndex={0} aria-label="Dynamic product attributes">
                    <table className="compact-table attribute-table">
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
                ) : (
                  <p className="muted">No attributes.</p>
                )}
              </article>

              <article className="raw-payload">
                <div className="panel-heading">
                  <FileText size={16} />
                  <h2>Raw payload preview (source)</h2>
                </div>
                <pre>{JSON.stringify(product.source_row, null, 2)}</pre>
              </article>
            </section>
          </div>
        </>
      )}
    </main>
  );
}
