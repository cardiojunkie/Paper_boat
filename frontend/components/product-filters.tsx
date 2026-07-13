"use client";

import { RotateCcw } from "lucide-react";
import { useQueries } from "@tanstack/react-query";

import { getFilterOptions } from "../lib/api";
import type { ProductFilters } from "../lib/types";

const fields = ["category", "product_type", "attribute_set", "l1", "l2", "l3", "l4"] as const;
const labels: Record<string, string> = { l1: "Category L1", l2: "Category L2", l3: "Category L3", l4: "Category L4" };

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
    <div className="filter-panel">
      <div className="filter-panel-heading">
        <span>Catalog fields</span>
        <button className="text-button" onClick={() => onChange(emptyFilters())} title="Clear all filters">
          <RotateCcw size={14} /> Clear
        </button>
      </div>
      <div className="filter-fields">
        {fields.map((field, index) => (
          <label key={field}>
            <span>{title(field)}</span>
            <select
              className="select"
              value={filters[field][0] ?? ""}
              onChange={(event) => onChange({ ...filters, [field]: event.target.value ? [event.target.value] : [] })}
            >
              <option value="">All</option>
              {(options[index].data?.values ?? []).map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
    </div>
  );
}
