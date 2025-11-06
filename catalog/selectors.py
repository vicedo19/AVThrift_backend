"""Selectors for catalog domain.

Read-only query helpers will be defined here to separate query logic
from services and views.

Expected selectors (sketch only):
- list_categories(ordering, include_counts=False)
- get_category_by_slug(slug)
- list_products(filters: category, price_range, attributes, search, ordering, pagination)
- get_product_by_slug(slug)
- list_collections(ordering)
- get_collection_by_slug(slug)
- list_attributes(filterable_only=True)
"""
