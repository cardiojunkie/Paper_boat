import pytest

from backend.app.excel import normalize_header, parse_xlsx
from backend.tests.conftest import workbook_bytes


def test_header_normalization_aliases() -> None:
    assert normalize_header(" Product   Type ") == "product type"
    assert normalize_header("attribute_set") == "attribute set"


def test_parse_preserves_unknown_headers_and_blank_cells() -> None:
    content = workbook_bytes(["SKU", "Product Type", "Mystery"], [["00123", "Phone", None]])
    result = parse_xlsx(content, "products.xlsx", 100)

    row = result.valid_rows[0]
    assert row.sku == "00123"
    assert row.core["product_type"] == "Phone"
    assert row.attributes == {"Mystery": None}
    assert row.source_row["SKU"] == "00123"


def test_parse_search_query_aliases() -> None:
    content = workbook_bytes(["SKU", "search_query"], [["00123", "washing machine"]])
    result = parse_xlsx(content, "products.xlsx", 100)

    assert result.valid_rows[0].core["search_query"] == "washing machine"


def test_missing_sku_header_fails() -> None:
    with pytest.raises(ValueError, match="Missing SKU"):
        parse_xlsx(workbook_bytes(["Title"], [["No SKU"]]), "products.xlsx", 100)


def test_missing_and_duplicate_skus_are_errors() -> None:
    content = workbook_bytes(["SKU", "Title"], [["A1", "First"], [None, "Bad"], ["A1", "Duplicate"]])
    result = parse_xlsx(content, "products.xlsx", 100)

    assert result.valid_rows == []
    assert {error.error_code for error in result.errors} == {"missing_sku", "duplicate_sku"}
    assert result.duplicate_skus == [{"sku": "A1", "rows": [2, 4]}]


def test_invalid_extension_rejected() -> None:
    with pytest.raises(ValueError, match="Only .xlsx"):
        parse_xlsx(b"not excel", "products.xls", 100)
