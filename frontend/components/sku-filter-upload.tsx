"use client";

import { Upload, X } from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { uploadSkuFilter } from "../lib/api";
import type { ProductFilters } from "../lib/types";

export function SkuFilterUpload({ filters, onChange }: { filters: ProductFilters; onChange: (filters: ProductFilters) => void }) {
  const mutation = useMutation({ mutationFn: uploadSkuFilter });
  const result = mutation.data;

  return (
    <div className="sku-filter-panel">
      <strong>SKU list</strong>
      <div className="filter-upload-actions">
        <label className="button">
          <Upload size={15} /> Upload file
          <input
            hidden
            type="file"
            accept=".xls,.xlsx"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              mutation.mutate(file, {
                onSuccess(data) {
                  onChange({ ...filters, sku_filter_token: data.token });
                },
              });
            }}
          />
        </label>
        {filters.sku_filter_token && (
          <button className="icon-button" aria-label="Clear SKU file filter" onClick={() => onChange({ ...filters, sku_filter_token: undefined })}>
            <X size={16} />
          </button>
        )}
        {mutation.isPending && <span className="muted">Reading SKU filter...</span>}
        {mutation.error && <span className="error">{mutation.error.message}</span>}
      </div>
      {result && (
        <p className="muted filter-note">
          Read {result.read_count} SKUs. {result.existing_count} exist, {result.missing_count} not found,{" "}
          {result.malformed_rows.length} malformed rows.
        </p>
      )}
    </div>
  );
}
