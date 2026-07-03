"use client";

import { ExternalLink, RotateCcw, Save } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  getProduct,
  getProductScrapeResults,
  getScrapeMarkdown,
  scrapeMarkdownUrl,
  updateScrapeMarkdown,
} from "../../../lib/api";

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
    <main className="page product-workspace">
      {query.isLoading && <div className="panel muted">Loading product...</div>}
      {query.error && <div className="panel error">{query.error.message}</div>}
      {product && (
        <>
          <header className="workspace-header">
            <div>
              <h1>{product.sku}</h1>
              <p className="muted">{product.title}</p>
            </div>
            <div className="status-pill">{results.length} scrape results</div>
          </header>

          <section className="workspace-grid">
            <div className="panel">
              <h2>Product</h2>
              <div className="detail-grid">
                {detailFields.map(([label, value]) => (
                  <div key={label}>
                    <strong>{label}</strong>
                    <div className="detail-value">{String(value ?? "")}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <h2>Scrape results</h2>
              {scrapeResults.isLoading && <p className="muted">Loading scrape results...</p>}
              {scrapeResults.error && <p className="error">{scrapeResults.error.message}</p>}
              {!scrapeResults.isLoading && !results.length && <p className="muted">No scrape results yet.</p>}
              {!!results.length && (
                <div className="result-list">
                  {results.map((result) => (
                    <button
                      key={result.id}
                      className={`result-button${selectedResult?.id === result.id ? " active" : ""}`}
                      onClick={() => setSelectedResultId(result.id)}
                    >
                      <strong>{result.marketplace}</strong>
                      <span>{result.status}</span>
                      <span>{result.result_count} results</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {selectedResult && (
              <>
                <div className="panel span-2">
                  <div className="row between">
                    <h2>{selectedResult.marketplace} result</h2>
                    <span className="status-pill">{selectedResult.status}</span>
                  </div>
                  <div className="field-block">
                    <strong>Search URL</strong>
                    <a className="url" href={selectedResult.search_url} target="_blank" rel="noreferrer">
                      {selectedResult.search_url}
                    </a>
                  </div>
                  {selectedResult.error_message && <p className="error">{selectedResult.error_message}</p>}
                  {!!selectedResult.items.length && (
                    <div className="table-wrap">
                      <table className="compact-table">
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Title</th>
                            <th>Price</th>
                            <th>URL</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedResult.items.map((item) => (
                            <tr key={`${item.position}-${item.url}`}>
                              <td>{item.position}</td>
                              <td>{item.title}</td>
                              <td>{item.price ?? ""}</td>
                              <td>
                                <a className="url" href={item.url} target="_blank" rel="noreferrer">
                                  {item.url}
                                </a>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                <div className="panel span-2">
                  <div className="row between">
                    <h2>Markdown</h2>
                    <div className="row">
                      {selectedResult.markdown_path ? (
                        <a className="button" href={scrapeMarkdownUrl(selectedResult.id)} target="_blank" rel="noreferrer">
                          <ExternalLink size={16} /> Open raw
                        </a>
                      ) : (
                        <button className="button" disabled>
                          <ExternalLink size={16} /> Open raw
                        </button>
                      )}
                      <button className="button" disabled={!selectedResult.markdown_path || markdown.isLoading} onClick={() => setDraft(markdown.data ?? "")}>
                        <RotateCcw size={16} /> Reset
                      </button>
                      <button
                        className="button primary"
                        disabled={!canSave || saveMarkdown.isPending}
                        onClick={() => saveMarkdown.mutate({ id: selectedResult.id, content: draft })}
                      >
                        <Save size={16} /> Save
                      </button>
                    </div>
                  </div>
                  {markdown.isLoading && <p className="muted">Loading markdown...</p>}
                  {markdown.error && <p className="error">{markdown.error.message}</p>}
                  {saveMarkdown.error && <p className="error">{saveMarkdown.error.message}</p>}
                  {message && <p className="muted">{message}</p>}
                  {!selectedResult.markdown_path && <p className="muted">Markdown has not been generated.</p>}
                  {selectedResult.markdown_path && (
                    <textarea
                      className="input markdown-editor"
                      value={draft}
                      onChange={(event) => {
                        setDraft(event.target.value);
                        setMessage("");
                      }}
                    />
                  )}
                </div>
              </>
            )}

            <div className="panel">
              <div className="row between">
                <h2>Dynamic attributes</h2>
                <input
                  className="input"
                  placeholder="Search attributes"
                  value={attributeSearch}
                  onChange={(event) => setAttributeSearch(event.target.value)}
                />
              </div>
              {!!attributes.length ? (
                <table className="compact-table">
                  <tbody>
                    {attributes.map(([key, value]) => (
                      <tr key={key}>
                        <th>{key}</th>
                        <td>{value == null ? "" : String(value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="muted">No attributes.</p>
              )}
            </div>

            <div className="panel">
              <h2>Source row</h2>
              <pre>{JSON.stringify(product.source_row, null, 2)}</pre>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
