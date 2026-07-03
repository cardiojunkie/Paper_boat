import pytest
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


def test_carrefour_extracts_top_10_with_prices(monkeypatch) -> None:
    from backend.app.config import settings

    html = "".join(
        f"""
        <div class="relative flex gap-2xs md:gap-1.5xs px-2xs flex-col" style="grid-column:span 3">
          <a class="w-full" tabindex="-1" href="/mafuae/en/category/product-{i}/p/22677{i:02d}?offer=offer_{i}">
            <img alt="Product image {i}">
          </a>
          <a tabindex="0" href="/mafuae/en/category/product-{i}/p/22677{i:02d}?offer=offer_{i}">
            <div class="text-sm leading-4 font-medium line-clamp-2 text-left md:text-md">Carrefour Product {i}</div>
          </a>
          <div class="flex flex-wrap gap-2xs">
            <div class="flex">
              <span class="text-lg leading-5 font-bold md:text-xl">{i:,}</span>
              <div class="flex flex-col">
                <div class="text-2xs font-bold leading-[10px]">.00</div>
                <div class="text-2xs font-medium leading-[10px]">AED</div>
              </div>
            </div>
          </div>
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

    items = scrape_marketplace("carrefour", "https://www.carrefouruae.com/mafuae/en/search?keyword=oven")

    assert calls == {"url": "https://www.carrefouruae.com/mafuae/en/search?keyword=oven", "timeout": settings.scrape_timeout_seconds}
    assert len(items) == 10
    assert items[0] == ScrapedItem(
        1,
        "Carrefour Product 0",
        "https://www.carrefouruae.com/mafuae/en/category/product-0/p/2267700?offer=offer_0",
        "AED 0.00",
    )
    assert items[-1] == ScrapedItem(
        10,
        "Carrefour Product 9",
        "https://www.carrefouruae.com/mafuae/en/category/product-9/p/2267709?offer=offer_9",
        "AED 9.00",
    )


def test_sharafdg_extracts_top_10_with_prices(monkeypatch) -> None:
    from backend.app.config import settings

    html = (
        '<div class="search-results col-md-9"><div class="product-items row reset-margin" id="hits">'
        + "".join(
            f"""
            <div class="slide product-wrapper col-md-3 reset-padding algolia-item">
              <a href="//uae.sharafdg.com/product/product-{i}/?promo={i}" title="Ignored attribute {i}" class="ratio-box product-link" data-objectid="sdg-{i}">
                <div class="hover-actions">
                  <div class="carousel-details">
                    <div class="slider--prd-info"><h4 class="name">Sharaf Product {i}</h4></div>
                  </div>
                </div>
                <div class="slider-extra--wrp">
                  <div class="product-price"><div class="price"><span class="currency_symbol dirham">D</span>&nbsp;{699 + i}.00</div></div>
                </div>
              </a>
            </div>
            """
            for i in range(11)
        )
        + "</div></div>"
    )
    calls = {}

    def fake_get(cls, url, **kwargs):
        calls["url"] = url
        calls["timeout"] = kwargs.get("timeout")
        return Adaptor(html, url=url)

    monkeypatch.setattr(settings, "scrape_max_results", 10)
    monkeypatch.setattr(scraper.Fetcher, "get", classmethod(fake_get))

    items = scrape_marketplace("sharafdg", "https://uae.sharafdg.com/?q=washer&post_type=product")

    assert calls == {"url": "https://uae.sharafdg.com/?q=washer&post_type=product", "timeout": settings.scrape_timeout_seconds}
    assert len(items) == 10
    assert items[0] == ScrapedItem(1, "Sharaf Product 0", "https://uae.sharafdg.com/product/product-0/?promo=0", "AED 699.00")
    assert items[-1] == ScrapedItem(10, "Sharaf Product 9", "https://uae.sharafdg.com/product/product-9/?promo=9", "AED 708.00")


def test_noon_extracts_top_10_with_prices(monkeypatch) -> None:
    from backend.app.config import settings

    html = "".join(
        f"""
        <a href="/uae-en/noon-product-{i}/N{i:08d}V/p/?o=offer{i}">
          <div data-qa="product-name">Noon Product {i}</div>
          <div data-qa="plp-product-box-price">
            <div><span class="_currency_1o2w0_30"></span><strong class="_amount_1o2w0_59">{2599 + i:,}</strong></div>
            <div><span class="_oldPrice_1o2w0_85 strikeThrough">2,799</span><span>7% Off</span></div>
          </div>
        </a>
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

    items = scrape_marketplace("noon", "https://www.noon.com/uae-en/search/?q=washer")

    assert calls == {"url": "https://www.noon.com/uae-en/search/?q=washer", "timeout": settings.scrape_timeout_seconds}
    assert len(items) == 10
    assert items[0] == ScrapedItem(1, "Noon Product 0", "https://www.noon.com/uae-en/noon-product-0/N00000000V/p/?o=offer0", "AED 2,599")
    assert items[-1] == ScrapedItem(10, "Noon Product 9", "https://www.noon.com/uae-en/noon-product-9/N00000009V/p/?o=offer9", "AED 2,608")


def test_noon_akamai_privacy_page_fails(monkeypatch) -> None:
    def fake_get(cls, url, **kwargs):
        return Adaptor('<a href="https://www.akamai.com/privacy">Privacy</a>', url=url)

    monkeypatch.setattr(scraper.Fetcher, "get", classmethod(fake_get))

    with pytest.raises(RuntimeError, match="Noon blocked request"):
        scrape_marketplace("noon", "https://www.noon.com/uae-en/search/?q=washer")
