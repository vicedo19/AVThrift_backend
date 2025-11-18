# Backend Implementation Portfolio

A running log of the backend features I’ve implemented for AVThrift. Written like a portfolio to show approach, craft, and breadth. I’ll keep this updated as we build more.

## Stack and Conventions
- Django 5 + Django REST Framework
- drf-spectacular for OpenAPI schema and live docs
- Auth: SimpleJWT for API; Django sessions for admin
- Packaging: UV; Formatting: Black + isort; Linting: Flake8; Hooks: pre-commit
- Config: python-decouple with env-driven settings
- Tests: pytest + pytest-django, factory_boy

## Architecture
- Bounded contexts:
  - Catalog (product identity, merchandising, search)
  - Inventory (stock state, movements, availability)
- Thin views, fat selectors/services:
  - Selectors for read-only queries (optimized prefetch, reusable)
  - Services for mutations and side-effects (atomic, validated)

## Catalog Domain
- Data modeling
  - Category hierarchy with `parent` → `children`
  - Product with SEO fields and Many-to-Many categories
  - ProductVariant with `sku`, `options`, and SKU-level pricing
  - Attributes + ProductAttributeValue for facets (supports product OR variant values)
  - Media model with `is_primary` and `sort_order` for product/variant imagery
  - Collection + through model `CollectionProduct` for curated ordering
- Constraints and Indexes (data integrity + performance)
  - XOR check: exactly one of `product` or `variant` on ProductAttributeValue
  - Unique primary media per product and per variant (conditional unique constraints)
  - Indexes on media (`product, sort_order, is_primary`), collection order (`collection, sort_order`), attributes (`attribute, product, variant`)
- API behavior
  - Products list: filters (category, status, currency, price range), search (`title`, `description`, `categories__name`), ordering, pagination
  - Product detail: categories, media, and stable shortcut fields (`primary_media_url`, `primary_category`)
  - Collections list/detail: curated product order via `CollectionProduct.sort_order`
  - Variants list/detail, Attributes list/detail
- Selectors (read logic)
  - `list_products`, `get_product_by_slug`, `list_categories`, `get_category_by_slug`
  - `list_collections`, `get_collection_with_ordered_products`
  - Nested helpers: `list_products_in_category`, `list_collection_products`, `list_variants_by_product_slug`, `list_media_by_product_slug`
- Docs
  - drf-spectacular examples for list/detail endpoints
  - Separation between user endpoints and admin endpoints in Swagger tags (admin currently deferred)
- Tests
  - API tests verify filters, search, ordering, pagination
  - Constraint tests: single primary media per product/variant; XOR on AttributeValue

## Inventory Domain
- Data modeling
  - Warehouse
  - StockItem (per product/variant per warehouse) with `quantity`, `reserved`, `status`
  - StockMovement (in/out/adjust) with reason/reference and audit timestamps
- Services
  - `apply_movement` transactional service with validation (insufficient quantity guard, atomic updates, movement record creation)
- Selectors
  - `available_quantity_for_stock_item` and per-product stock listing
  - `list_warehouses` (active)
- Endpoints
  - Healthcheck and roadmap scaffolding to bootstrap the app namespace

## Security and Validation
- JWT for API auth; session auth for Django admin
- Input validation across serializers; parameter validation on list endpoints
- Database constraints to enforce invariants (media uniqueness, XOR attribute values)

## Performance Practices
- Selective prefetch (primary media + categories) for list endpoints
- Indexes on ordering and filtering columns
- Query count assertions in tests on critical endpoints

## Operational Care
- Pre-commit hooks for style and basic hygiene
- Env-driven settings (email backend, CORS/CSRF, database)
- Migrations managed and applied consistently; SQLite for dev, Postgres for prod

## What I’d Add Next
- Admin API (when ready): products/variants/media CRUD with role-based permissions and service-layer transactions
- Faceted filtering endpoint (computed attribute facets for search results)
- Availability overlay from Inventory into Catalog responses via selectors
- Observability: structured JSON logs and optional Sentry integration
- Bulk tools: curated order bulk update endpoints, media reorder actions

## Approach and Philosophy
- Keep views thin; isolate business logic in selectors/services
- Lock behavior with tests, especially around data integrity and performance
- Prefer explicitness and small, focused migrations; add indexes before optimizing code paths
- Document as we build to make onboarding and maintenance easy
