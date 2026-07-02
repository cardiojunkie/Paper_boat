from backend.app.scraper import ScrapedItem, build_search_url, safe_sku_filename, write_markdown


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
        [ScrapedItem(1, "Washer", "https://example.com/p")],
        None,
    )

    content = tmp_path.joinpath("SKU_1_amazon.md").read_text()
    assert path.endswith("SKU_1_amazon.md")
    assert "washing machine" in content
    assert "Washer" in content
