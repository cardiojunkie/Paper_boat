from sqlalchemy import Select, and_, func, select
from sqlalchemy.orm import Session

from .models import Product, SkuFilterToken
from .schemas import ProductFilter

FILTER_COLUMNS = {
    "product_type": Product.product_type,
    "attribute_set": Product.attribute_set,
    "category": Product.category,
    "l1": Product.l1,
    "l2": Product.l2,
    "l3": Product.l3,
    "l4": Product.l4,
}


def filter_conditions(db: Session, filters: ProductFilter) -> list:
    conditions = []
    if filters.sku_search:
        conditions.append(Product.sku.ilike(f"%{filters.sku_search.strip()}%"))
    if filters.title_search:
        conditions.append(Product.title.ilike(f"%{filters.title_search.strip()}%"))
    for name, column in FILTER_COLUMNS.items():
        values = getattr(filters, name)
        if values:
            conditions.append(column.in_(values))
    if filters.sku_filter_token:
        token = db.get(SkuFilterToken, filters.sku_filter_token)
        if token:
            conditions.append(Product.sku.in_(token.skus))
        else:
            conditions.append(Product.sku.in_([]))
    return conditions


def apply_product_filters(stmt: Select, db: Session, filters: ProductFilter) -> Select:
    conditions = filter_conditions(db, filters)
    return stmt.where(and_(*conditions)) if conditions else stmt


def count_products(db: Session, filters: ProductFilter) -> int:
    stmt = apply_product_filters(select(func.count()).select_from(Product), db, filters)
    return int(db.execute(stmt).scalar_one())
