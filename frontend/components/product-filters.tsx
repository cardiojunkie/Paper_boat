"use client";

import { RotateCcw } from "lucide-react";
import { useQueries } from "@tanstack/react-query";

import { getFilterOptions } from "../lib/api";
import type { ProductFilters } from "../lib/types";

const fields = ["product_type", "attribute_set", "l1", "l2", "l3", "l4"] as const;
const labels: Record<string, string> = { l1: "Cat L1", l2: "Cat L2", l3: "Cat L3", l4: "Cat L4" };

function title(field: string) {
  return labels[field] ?? field.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export function emptyFilters(): ProductFilters {
  return { product_type: [], attribute_set: [], category: [], l1: [], l2: [], l3: [], l4: [] };
}

export function ProductFiltersView({ filters, onChange }: { filters: ProductFilters; onChange: (filters: ProductFilters) => void }) {
  const options = useQueries({
    queries: fields.map((field) => ({
      queryKey: ["filter-options", field, filters],
      queryFn: () => getFilterOptions(field, filters),
    })),
  });

  return (
    <div className="toolbar">
      <div className="row">
        <input
          className="input"
          placeholder="Search SKU"
          value={filters.sku_search ?? ""}
          onChange={(event) => onChange({ ...filters, sku_search: event.target.value || undefined })}
        />
        <input
          className="input"
          placeholder="Search title"
          value={filters.title_search ?? ""}
          onChange={(event) => onChange({ ...filters, title_search: event.target.value || undefined })}
        />
        <button className="button" onClick={() => onChange(emptyFilters())} title="Clear all filters">
          <RotateCcw size={16} /> Clear
        </button>
      </div>
      <div className="row">
        {fields.map((field, index) => (
          <select
            key={field}
            className="select"
            value={filters[field][0] ?? ""}
            onChange={(event) => onChange({ ...filters, [field]: event.target.value ? [event.target.value] : [] })}
          >
            <option value="">{title(field)}</option>
            {(options[index].data?.values ?? []).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        ))}
      </div>
    </div>
  );
}
