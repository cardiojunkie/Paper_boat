from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from re import sub
from time import sleep
from urllib.parse import quote, quote_plus, urljoin

from scrapling.fetchers import Fetcher
from scrapling.parser import Adaptor

from .config import settings


MARKETPLACES = {
    "amazon": {
        "label": "Amazon AE",
        "template": "https://www.amazon.ae/s?k={query_plus}",
        "selectors": ["[data-component-type='s-search-result'] a.a-link-normal.s-no-outline", "h2 a"],
    },
    "noon": {
        "label": "Noon UAE",
        "template": "https://www.noon.com/uae-en/search/?q={query_plus}",
        "selectors": ["a[href*='/uae-en/'][href*='/p/']", "a[href*='/p/']"],
    },
    "sharafdg": {
        "label": "Sharaf DG",
        "template": "https://uae.sharafdg.com/?q={query_percent}&post_type=product",
        "selectors": ["a.woocommerce-LoopProduct-link", "a[href*='/product/']"],
    },
    "carrefour": {
        "label": "Carrefour UAE",
        "template": "https://www.carrefouruae.com/mafuae/en/search?keyword={query_percent}",
        "selectors": ["a[href*='/mafuae/en/'][href*='/p/']", "a[href*='/p/']"],
    },
}


@dataclass(frozen=True)
class ScrapedItem:
    position: int
    title: str
    url: str


def build_search_url(marketplace: str, query: str) -> str:
    template = MARKETPLACES[marketplace]["template"]
    return template.format(query_plus=quote_plus(query), query_percent=quote(query))


def safe_sku_filename(sku: str) -> str:
    cleaned = sub(r"[^A-Za-z0-9._-]+", "_", sku.strip())
    return cleaned.strip("._") or "sku"


def _text(selector) -> str:
    text = selector.get_all_text(separator=" ", strip=True)
    return sub(r"\s+", " ", text).strip()


def _items_from_page(page: Adaptor, marketplace: str, search_url: str) -> list[ScrapedItem]:
    seen: set[str] = set()
    items: list[ScrapedItem] = []
    selectors = [*MARKETPLACES[marketplace]["selectors"], "a[href]"]
    for css in selectors:
        for link in page.css(css):
            href = link.attrib.get("href")
            title = _text(link)
            if not href or not title:
                continue
            absolute = urljoin(search_url, href)
            if absolute in seen:
                continue
            seen.add(absolute)
            items.append(ScrapedItem(len(items) + 1, title, absolute))
            if len(items) >= settings.scrape_max_results:
                return items
    return items


def scrape_marketplace(marketplace: str, search_url: str) -> list[ScrapedItem]:
    Fetcher.configure(timeout=settings.scrape_timeout_seconds)
    page = Fetcher().get(search_url)
    if settings.scrape_delay_seconds:
        sleep(settings.scrape_delay_seconds)
    return _items_from_page(page, marketplace, search_url)


def write_markdown(sku: str, marketplace: str, search_query: str, search_url: str, items: list[ScrapedItem], error: str | None) -> str:
    output_dir = Path(settings.scrape_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_sku_filename(sku)}_{marketplace}.md"
    lines = [
        f"# {sku} - {MARKETPLACES[marketplace]['label']}",
        "",
        f"- SKU: `{sku}`",
        f"- Marketplace: `{marketplace}`",
        f"- Search query: `{search_query}`",
        f"- Search URL: {search_url}",
        f"- Generated at: {datetime.now(UTC).isoformat()}",
        "",
    ]
    if error:
        lines.extend(["## Error", "", error, ""])
    else:
        lines.extend(["## Results", ""])
        if not items:
            lines.append("No products found.")
        for item in items:
            lines.append(f"{item.position}. [{item.title}]({item.url})")
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
