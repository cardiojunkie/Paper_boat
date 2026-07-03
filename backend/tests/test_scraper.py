from scrapling.parser import Adaptor

from backend.app import scraper
from backend.app.scraper import ScrapedItem, build_search_url, safe_sku_filename, scrape_marketplace, write_markdown


def test_search_urls_match_marketplaces() -> None:
    assert build_search_url("amazon", "washing machine") == "https://www.amazon.ae/s?k=washing+machine"
    assert build_search_url("noon", "washing machine") == "https://www.noon.com/uae-en/search/?q=washing+machine"
    assert build_search_url("sharafdg", "washing machine") == "https://uae.sharafdg.com/?q=washing%20machine&post_type=product"
    assert build_search_url("carrefour", "washing machine") == "https://www.carrefouruae.com/mafuae/en/search?keyword=washing%20machine"


def test_special_characters_are_encoded() -> None:
    assert "a%2Bb" in build_search_url("carrefour", "a+b")
    assert "a%2Bb" in build_search_url("sharafdg", "a+b")
    assert "a%2Bb" in build_search_url("amazon", "a+b")


def test_safe_sku_filename() -> None:
    assert safe_sku_filename("SKU/1 2") == "SKU_1_2"


def test_markdown_writer(tmp_path, monkeypatch) -> None:
    from backend.app.config import settings

    monkeypatch.setattr(settings, "scrape_output_dir", str(tmp_path))
    path = write_markdown(
        "SKU/1",
        "amazon",
        "washing machine",
        "https://example.com",
        [ScrapedItem(1, "Washer", "https://example.com/p", "AED 99.00")],
        None,
    )

    content = tmp_path.joinpath("SKU_1_amazon.md").read_text()
    assert path.endswith("SKU_1_amazon.md")
    assert "washing machine" in content
    assert "Washer" in content
    assert "AED 99.00" in content


def test_amazon_extracts_top_10_with_prices(monkeypatch) -> None:
    from backend.app.config import settings

    html = "".join(
        f"""
        <div data-cy="asin-faceout-container" data-asin="B0000000{i:02d}">
          <a href="/Example/dp/B0000000{i:02d}/ref=sr_1_{i}"><img></a>
          <a href="/Example/dp/B0000000{i:02d}/ref=sr_1_{i}">
            <h2 aria-label="Product {i}"><span>Ignored</span></h2>
          </a>
          <span class="a-price"><span class="a-offscreen">AED {i}.00</span></span>
        </div>
        """
        for i in range(11)
    )
    calls = {}

    def fake_get(cls, url, **kwargs):
        calls["url"] = url
        calls["timeout"] = kwargs.get("timeout")
        return Adaptor(html, url=url)

    monkeypatch.setattr(settings, "scrape_max_results", 10)
    monkeypatch.setattr(scraper.Fetcher, "get", classmethod(fake_get))

    items = scrape_marketplace("amazon", "https://www.amazon.ae/s?k=oven")

    assert calls == {"url": "https://www.amazon.ae/s?k=oven", "timeout": settings.scrape_timeout_seconds}
    assert len(items) == 10
    assert items[0] == ScrapedItem(1, "Product 0", "https://www.amazon.ae/Example/dp/B000000000/ref=sr_1_0", "AED 0.00")
    assert items[-1].title == "Product 9"
