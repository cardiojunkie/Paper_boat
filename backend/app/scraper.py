from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from re import search, sub
from time import sleep
from urllib.parse import quote, quote_plus, urljoin

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


class Fetcher:
    # ponytail: lazy import keeps app/TestClient startup away from fetcher event-loop deps.
    @classmethod
    def get(cls, url: str, **kwargs):
        from scrapling.fetchers import Fetcher as ScraplingFetcher

        return ScraplingFetcher.get(url, **kwargs)


def build_search_url(marketplace: str, query: str) -> str:
    template = MARKETPLACES[marketplace]["template"]
    return template.format(query_plus=quote_plus(query), query_percent=quote(query))


def safe_sku_filename(sku: str) -> str:
    cleaned = sub(r"[^A-Za-z0-9._-]+", "_", sku.strip())
    return cleaned.strip("._") or "sku"


def _text(selector) -> str:
    text = selector.get_all_text(separator=" ", strip=True)
    return sub(r"\s+", " ", text).strip()


def _title(selector) -> str:
    for attr in ("aria-label", "title", "alt"):
        value = selector.attrib.get(attr, "").strip()
        if value:
            return value
    image = _first(selector, "img[alt]")
    if image:
        value = image.attrib.get("alt", "").strip()
        if value:
            return value
    return _text(selector)


def _first(selectors, css: str):
    matches = selectors.css(css)
    return matches[0] if matches else None


def _aed_price(text: str) -> str | None:
    cleaned = sub(r"^(D|\ue001)\s*", "AED ", text).strip()
    return cleaned or None


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
        links = [link for link in card.css("a[href*='/dp/']") if "#customerReviews" not in link.attrib.get("href", "")]
        link = next((candidate for candidate in links if _text(candidate)), links[0] if links else None)
        if not link:
            continue
        href = link.attrib.get("href", "")
        title_node = _first(card, "h2[aria-label]")
        title = _title(title_node) if title_node else _title(link)
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


def _carrefour_key(href: str) -> str:
    match = search(r"/p/([^/?#]+)", href)
    return match.group(1) if match else href


def _carrefour_price(card) -> str | None:
    whole_node = _first(card, "span[class*='text-lg']")
    whole = _text(whole_node) if whole_node else ""
    price_parts = [_text(part) for part in card.css("div[class*='text-2xs']")[:2]]
    if not whole or len(price_parts) < 2:
        return None
    fraction, currency = price_parts
    return f"{currency} {whole}{fraction}"


def _carrefour_items(page: Adaptor, search_url: str) -> list[ScrapedItem]:
    seen: set[str] = set()
    items: list[ScrapedItem] = []
    for card in page.css("div[style*='grid-column:span 3']"):
        link = next((link for link in card.css("a[href*='/mafuae/en/'][href*='/p/']") if _text(link)), None)
        if not link:
            continue
        href = link.attrib.get("href", "")
        title_node = _first(link, "div[class*='line-clamp-2']")
        title = _text(title_node) if title_node else _text(link)
        if not href or not title:
            continue
        key = _carrefour_key(href)
        if key in seen:
            continue
        seen.add(key)
        items.append(ScrapedItem(len(items) + 1, title, urljoin(search_url, href), _carrefour_price(card)))
        if len(items) >= settings.scrape_max_results:
            return items
    return items


def _sharafdg_items(page: Adaptor, search_url: str) -> list[ScrapedItem]:
    seen: set[str] = set()
    items: list[ScrapedItem] = []
    for card in page.css("#hits .algolia-item, .algolia-item"):
        link = _first(card, "a.product-link[href]")
        if not link:
            continue
        href = link.attrib.get("href", "")
        title_node = _first(link, "h4.name")
        title = (_text(title_node) if title_node else "") or link.attrib.get("title", "").strip() or _text(link)
        if not href or not title:
            continue
        key = link.attrib.get("data-objectid") or href
        if key in seen:
            continue
        seen.add(key)
        price_node = _first(card, ".product-price .price")
        items.append(ScrapedItem(len(items) + 1, title, urljoin(search_url, href), _aed_price(_text(price_node)) if price_node else None))
        if len(items) >= settings.scrape_max_results:
            return items
    return items


def _noon_blocked(page: Adaptor) -> bool:
    return bool(page.css("a[href*='akamai.com/privacy']")) and not page.css("a[href*='/uae-en/'][href*='/p/']")


def _blocked_reason(page: Adaptor, marketplace: str) -> str | None:
    if marketplace == "noon" and _noon_blocked(page):
        return "Akamai privacy page"
    status = getattr(page, "status", None)
    if status and int(status) >= 400:
        return f"HTTP {status}"
    text = _text(page).lower()
    if not text and not page.css("a[href]"):
        return "empty response"
    blocked_markers = (
        "access denied",
        "captcha",
        "enable javascript",
        "enter the characters you see below",
        "service unavailable",
        "verify you are human",
    )
    if any(marker in text for marker in blocked_markers):
        return "challenge page"
    return None


def _noon_price(card) -> tuple[str | None, str]:
    amount_node = _first(card, "[data-qa='plp-product-box-price'] strong[class*='_amount']")
    amount = _text(amount_node) if amount_node else ""
    return (f"AED {amount}" if amount else None, amount)


def _noon_title(card, amount: str) -> str:
    for css in ["[data-qa='product-name']", "[data-qa='plp-product-name']", "[class*='productName']", "[class*='title']"]:
        node = _first(card, css)
        if node:
            return _text(node)
    title = _text(card)
    if amount and amount in title:
        title = title.split(amount, 1)[0]
    return sub(r"\ue001\s*$", "", title).strip()


def _noon_key(href: str) -> str:
    match = search(r"/([^/]+)/p/", href)
    return match.group(1) if match else href


def _noon_items(page: Adaptor, search_url: str) -> list[ScrapedItem]:
    seen: set[str] = set()
    items: list[ScrapedItem] = []
    for link in page.css("a[href*='/uae-en/'][href*='/p/']"):
        href = link.attrib.get("href", "")
        price, amount = _noon_price(link)
        title = _noon_title(link, amount)
        if not href or not title:
            continue
        key = _noon_key(href)
        if key in seen:
            continue
        seen.add(key)
        items.append(ScrapedItem(len(items) + 1, title, urljoin(search_url, href), price))
        if len(items) >= settings.scrape_max_results:
            return items
    return items


def _items_from_page(page: Adaptor, marketplace: str, search_url: str) -> list[ScrapedItem]:
    reason = _blocked_reason(page, marketplace)
    if reason:
        raise RuntimeError(f"{MARKETPLACES[marketplace]['label']} blocked request: {reason}")

    if marketplace == "amazon":
        items = _amazon_items(page, search_url)
        if items:
            return items
    if marketplace == "noon":
        items = _noon_items(page, search_url)
        if items:
            return items
    if marketplace == "sharafdg":
        items = _sharafdg_items(page, search_url)
        if items:
            return items
    if marketplace == "carrefour":
        items = _carrefour_items(page, search_url)
        if items:
            return items

    seen: set[str] = set()
    items: list[ScrapedItem] = []
    selectors = [*MARKETPLACES[marketplace]["selectors"], "a[href]"]
    for css in selectors:
        for link in page.css(css):
            href = link.attrib.get("href")
            title = _title(link)
            if not href or not title:
                continue
            absolute = urljoin(search_url, href)
            if absolute in seen:
                continue
            seen.add(absolute)
            items.append(ScrapedItem(len(items) + 1, title, absolute))
            if len(items) >= settings.scrape_max_results:
                return items
    raise RuntimeError(f"{MARKETPLACES[marketplace]['label']} returned no product results")


def scrape_marketplace(marketplace: str, search_url: str) -> list[ScrapedItem]:
    page = Fetcher.get(search_url, timeout=settings.scrape_timeout_seconds, follow_redirects=True)
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
