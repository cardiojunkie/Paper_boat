"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
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
    <main className="page product-workspace">
      <header className="workspace-header">
        <div>
          <h1>Products</h1>
          <p className="muted">Catalog workspace</p>
        </div>
        <div className="row">
          <span className="status-pill">{total} products</span>
          <span className="status-pill">{selectedIds.length} selected</span>
        </div>
      </header>

      <section className="workspace-grid">
        <div className="grid">
          <ImportUpload onImported={resetAfterImport} />
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
        </div>

        <div className="grid">
          <DeleteControls selectedIds={selectedIds} filters={filters} onDeleted={clearSelection} />
          <OpenRouterSettings />
          <ScrapeControls selectedIds={selectedIds} onStaleSelection={clearSelection} />
        </div>

        <div className="span-2">
          <div className="panel">
            <div className="row between">
              <div className="row">
                <select className="select" value={sort} onChange={(event) => setSort(event.target.value)}>
                  <option value="updated_at">Updated</option>
                  <option value="created_at">Created</option>
                  <option value="sku">SKU</option>
                  <option value="title">Title</option>
                </select>
                <select className="select" value={direction} onChange={(event) => setDirection(event.target.value)}>
                  <option value="desc">Desc</option>
                  <option value="asc">Asc</option>
                </select>
                <select className="select" value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
                  {[25, 50, 100, 250].map((size) => (
                    <option key={size} value={size}>
                      {size} rows
                    </option>
                  ))}
                </select>
              </div>
              <span className="muted">{total} total products</span>
            </div>
          </div>
          {query.isLoading && <div className="panel muted">Loading products...</div>}
          {query.error && <div className="panel error">{query.error.message}</div>}
          {query.data && <ProductTable items={query.data.items} selected={selected} onSelectedChange={setSelected} />}
          <div className="panel row between">
            <button className="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button className="button" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>
              Next
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
