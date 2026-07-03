import { z } from "zod";

import type {
  ImportResult,
  Marketplace,
  ProductDetail,
  ProductFilters,
  ProductListResponse,
  ScrapeJob,
  ScrapeJobCreateResponse,
  ScrapeResult,
  SkuFilterResult,
} from "./types";

const API_BASE = "";

export const filterSchema = z.object({
  sku_search: z.string().optional(),
  title_search: z.string().optional(),
  product_type: z.array(z.string()).default([]),
  attribute_set: z.array(z.string()).default([]),
  category: z.array(z.string()).default([]),
  l1: z.array(z.string()).default([]),
  l2: z.array(z.string()).default([]),
  l3: z.array(z.string()).default([]),
  l4: z.array(z.string()).default([]),
  sku_filter_token: z.string().optional(),
});

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? response.statusText);
  }
  return response.json() as Promise<T>;
}

function appendFilters(params: URLSearchParams, filters: ProductFilters) {
  const parsed = filterSchema.parse(filters);
  Object.entries(parsed).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => params.append(key, item));
    } else if (value) {
      params.set(key, value);
    }
  });
}

export function listProducts(filters: ProductFilters, page: number, pageSize: number, sort: string, direction: string) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize), sort, direction });
  appendFilters(params, filters);
  return request<ProductListResponse>(`/api/products?${params}`);
}

export function getProduct(id: string) {
  return request<ProductDetail>(`/api/products/${id}`);
}

export function getMarketplaces() {
  return request<Marketplace[]>("/api/marketplaces");
}

export function createScrapeJob(productIds: string[], marketplaces: Marketplace["key"][]) {
  return request<ScrapeJobCreateResponse>("/api/scrape-jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_ids: productIds, marketplaces }),
  });
}

export function getScrapeJob(id: string) {
  return request<ScrapeJob>(`/api/scrape-jobs/${id}`);
}

export function getProductScrapeResults(productId: string) {
  return request<ScrapeResult[]>(`/api/products/${productId}/scrape-results`);
}

export function scrapeMarkdownUrl(resultId: string) {
  return `/api/scrape-results/${resultId}/markdown`;
}

export async function getScrapeMarkdown(resultId: string) {
  const response = await fetch(scrapeMarkdownUrl(resultId));
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? response.statusText);
  }
  return response.text();
}

export function updateScrapeMarkdown(resultId: string, content: string) {
  return request<{ content: string }>(scrapeMarkdownUrl(resultId), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

export function getFilterOptions(field: string, filters: ProductFilters) {
  const params = new URLSearchParams({ field });
  appendFilters(params, filters);
  return request<{ field: string; values: string[] }>(`/api/products/filter-options?${params}`);
}

export function uploadImport(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<ImportResult>("/api/imports/products", { method: "POST", body: form });
}

export function uploadSkuFilter(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<SkuFilterResult>("/api/product-filters/sku-file", { method: "POST", body: form });
}

export function deleteSelected(ids: string[]) {
  return request<{ deleted_count: number; audit_id: string }>("/api/products/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids, skus: [], confirmation: `DELETE ${ids.length} PRODUCTS` }),
  });
}

export async function previewDelete(filters: ProductFilters) {
  return request<{ count: number; confirmation_phrase: string }>("/api/products/delete-preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filters: filterSchema.parse(filters) }),
  });
}

export function deleteByFilter(filters: ProductFilters, expectedCount: number, confirmation: string) {
  return request<{ deleted_count: number; audit_id: string }>("/api/products/delete-by-filter", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filters: filterSchema.parse(filters), expected_count: expectedCount, confirmation }),
  });
}
