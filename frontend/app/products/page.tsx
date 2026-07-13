"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";

import { DeleteControls } from "../../components/delete-dialog";
import { ImportUpload } from "../../components/import-upload";
import { OpenRouterSettings } from "../../components/openrouter-settings";
import { emptyFilters, ProductFiltersView } from "../../components/product-filters";
import { ProductTable } from "../../components/product-table";
import { SkuFilterUpload } from "../../components/sku-filter-upload";
import { ScrapeControls } from "../../components/scrape-controls";
import { listProducts } from "../../lib/api";

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState(emptyFilters());
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [sort, setSort] = useState("updated_at");
  const [direction, setDirection] = useState("desc");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const clearSelection = () => setSelected({});
  const query = useQuery({
    queryKey: ["products", filters, page, pageSize, sort, direction],
    queryFn: () => listProducts(filters, page, pageSize, sort, direction),
  });
  const selectedIds = useMemo(() => Object.entries(selected).filter(([, value]) => value).map(([id]) => id), [selected]);
  const totalPages = Math.max(1, Math.ceil((query.data?.total ?? 0) / pageSize));
  const total = query.data?.total ?? 0;
  const resetAfterImport = () => {
    setPage(1);
    clearSelection();
    queryClient.invalidateQueries({ queryKey: ["products"] });
    queryClient.invalidateQueries({ queryKey: ["filter-options"] });
  };

  return (
    <main className="products-page">
      <header className="workspace-topbar">
        <div className="workspace-title">
          <h1>Products Workspace</h1>
          <span className="topbar-divider" />
          <span>Total: <strong>{total.toLocaleString()}</strong></span>
          <span>Selected: <strong className="accent-text">{selectedIds.length}</strong></span>
        </div>
        <div className="workspace-searches">
          <label className="search-field">
            <Search size={16} />
            <span className="sr-only">Search by SKU</span>
            <input
              value={filters.sku_search ?? ""}
              placeholder="Search SKU"
              onChange={(event) => {
                setPage(1);
                clearSelection();
                setFilters({ ...filters, sku_search: event.target.value || undefined });
              }}
            />
          </label>
          <label className="search-field">
            <Search size={16} />
            <span className="sr-only">Search by title</span>
            <input
              value={filters.title_search ?? ""}
              placeholder="Search title"
              onChange={(event) => {
                setPage(1);
                clearSelection();
                setFilters({ ...filters, title_search: event.target.value || undefined });
              }}
            />
          </label>
        </div>
      </header>

      <section className="products-workspace">
        <aside className="filters-rail">
          <div className="rail-heading">
            <SlidersHorizontal size={16} />
            <strong>Filters</strong>
          </div>
          <ProductFiltersView
            filters={filters}
            onChange={(next) => {
              setPage(1);
              clearSelection();
              setFilters(next);
            }}
          />
          <SkuFilterUpload
            filters={filters}
            onChange={(next) => {
              clearSelection();
              setFilters(next);
            }}
          />
        </aside>

        <section className="data-canvas">
          <div className="action-deck">
            <div className="bulk-actions">
              <span className="selection-chip">{selectedIds.length} Selected</span>
              <span className="topbar-divider" />
              <ScrapeControls selectedIds={selectedIds} onStaleSelection={clearSelection} />
              <DeleteControls selectedIds={selectedIds} filters={filters} onDeleted={clearSelection} />
            </div>
            <div className="workspace-utilities">
              <ImportUpload onImported={resetAfterImport} />
              <details className="settings-drawer" id="llm-settings">
                <summary>LLM Settings</summary>
                <OpenRouterSettings />
              </details>
            </div>
          </div>

          <div className="table-toolbar">
            <div className="row">
              <label>
                <span className="sr-only">Sort products by</span>
                <select className="select" value={sort} onChange={(event) => setSort(event.target.value)}>
                  <option value="updated_at">Updated</option>
                  <option value="created_at">Created</option>
                  <option value="sku">SKU</option>
                  <option value="title">Title</option>
                </select>
              </label>
              <label>
                <span className="sr-only">Sort direction</span>
                <select className="select" value={direction} onChange={(event) => setDirection(event.target.value)}>
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </label>
              <label>
                <span className="sr-only">Rows per page</span>
                <select
                  className="select"
                  value={pageSize}
                  onChange={(event) => {
                    setPage(1);
                    setPageSize(Number(event.target.value));
                  }}
                >
                  {[25, 50, 100, 250].map((size) => (
                    <option key={size} value={size}>
                      {size} rows
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <span className="muted">{total.toLocaleString()} total products</span>
          </div>

          <div className="table-region">
            {query.isLoading && <div className="empty-state muted">Loading products...</div>}
            {query.error && <div className="empty-state error">{query.error.message}</div>}
            {query.data && <ProductTable items={query.data.items} selected={selected} onSelectedChange={setSelected} />}
          </div>

          <footer className="pagination-footer">
            <span className="muted">
              Showing {total ? (page - 1) * pageSize + 1 : 0}–{Math.min(page * pageSize, total)} of {total.toLocaleString()}
            </span>
            <div className="row">
              <button className="page-button" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
                <ChevronLeft size={17} />
              </button>
              <span className="page-current">{page}</span>
              <span className="muted">of {totalPages}</span>
              <button className="page-button" aria-label="Next page" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>
                <ChevronRight size={17} />
              </button>
            </div>
          </footer>
        </section>
      </section>
    </main>
  );
}
