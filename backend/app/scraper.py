from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from re import search, sub
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
    price: str | None = None


def build_search_url(marketplace: str, query: str) -> str:
    template = MARKETPLACES[marketplace]["template"]
    return template.format(query_plus=quote_plus(query), query_percent=quote(query))


def safe_sku_filename(sku: str) -> str:
    cleaned = sub(r"[^A-Za-z0-9._-]+", "_", sku.strip())
    return cleaned.strip("._") or "sku"


def _text(selector) -> str:
    text = selector.get_all_text(separator=" ", strip=True)
    return sub(r"\s+", " ", text).strip()


def _first(selectors, css: str):
    matches = selectors.css(css)
    return matches[0] if matches else None


def _asin(card, href: str) -> str:
    value = card.attrib.get("data-asin") or card.attrib.get("data-csa-c-item-id", "")
    if value.startswith("amzn1.asin."):
        value = value.rsplit(".", 1)[-1]
    match = search(r"/dp/([A-Z0-9]{10})", href)
    return value or (match.group(1) if match else href)


def _amazon_items(page: Adaptor, search_url: str) -> list[ScrapedItem]:
    seen: set[str] = set()
    items: list[ScrapedItem] = []
    cards = [
        *page.css("[data-cy='asin-faceout-container']"),
        *page.css("[data-component-type='s-search-result']"),
        *page.css("[data-cel-widget^='MAIN-SEARCH_RESULTS']"),
    ]
    for card in cards:
        link = _first(card, "a[href*='/dp/']")
        if not link:
            continue
        href = link.attrib.get("href", "")
        title_node = _first(card, "h2[aria-label]")
        title = title_node.attrib.get("aria-label", "").strip() if title_node else _text(link)
        if not href or not title:
            continue
        key = _asin(card, href)
        if key in seen:
            continue
        seen.add(key)
        price_node = _first(card, ".a-price .a-offscreen")
        items.append(ScrapedItem(len(items) + 1, title, urljoin(search_url, href), _text(price_node) if price_node else None))
        if len(items) >= settings.scrape_max_results:
            return items
    return items


def _items_from_page(page: Adaptor, marketplace: str, search_url: str) -> list[ScrapedItem]:
    if marketplace == "amazon":
        items = _amazon_items(page, search_url)
        if items:
            return items

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
    page = Fetcher.get(search_url, timeout=settings.scrape_timeout_seconds)
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
            price = f" - {item.price}" if item.price else ""
            lines.append(f"{item.position}. [{item.title}]({item.url}){price}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
