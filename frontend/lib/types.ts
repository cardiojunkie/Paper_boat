export type ProductListItem = {
  id: string;
  sku: string;
  title: string | null;
  category: string | null;
  product_type: string | null;
  attribute_set: string | null;
  l1: string | null;
  l2: string | null;
  l3: string | null;
  l4: string | null;
  search_query: string | null;
  updated_at: string;
};

export type ProductDetail = ProductListItem & {
  bullet_points: string | null;
  specs: string | null;
  attributes: Record<string, unknown>;
  source_row: Record<string, unknown>;
  source_filename: string | null;
  created_at: string;
};

export type ProductListResponse = {
  items: ProductListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type ProductFilters = {
  sku_search?: string;
  title_search?: string;
  product_type: string[];
  attribute_set: string[];
  category: string[];
  l1: string[];
  l2: string[];
  l3: string[];
  l4: string[];
  sku_filter_token?: string;
};

export type ImportResult = {
  id: string;
  original_filename: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  inserted_rows: number;
  updated_rows: number;
  failed_rows: number;
  warning_rows: number;
  duplicate_skus: unknown[];
  error_summary: string | null;
  errors: RowError[];
};

export type RowError = {
  row_number: number;
  sku: string | null;
  error_code: string;
  message: string;
  field_header: string | null;
};

export type SkuFilterResult = {
  token: string;
  read_count: number;
  existing_count: number;
  missing_count: number;
  malformed_rows: RowError[];
};

export type Marketplace = {
  key: "amazon" | "noon" | "sharafdg" | "carrefour";
  label: string;
  enabled: boolean;
};

export type ScrapeResultItem = {
  position: number;
  title: string;
  url: string;
};

export type ScrapeResult = {
  id: string;
  product_id: string;
  sku: string;
  marketplace: Marketplace["key"];
  search_query: string;
  search_url: string;
  status: string;
  result_count: number;
  markdown_path: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  items: ScrapeResultItem[];
};

export type ScrapeJob = {
  id: string;
  status: string;
  requested_product_ids: string[];
  marketplaces: string[];
  total_targets: number;
  completed_targets: number;
  failed_targets: number;
  started_at: string | null;
  completed_at: string | null;
  error_summary: string | null;
  results: ScrapeResult[];
};
