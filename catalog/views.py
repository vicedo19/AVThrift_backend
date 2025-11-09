"""Read-only viewsets for catalog resources (initial MVP)."""

from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from inventory.models import StockItem
from rest_framework import filters as drf_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import selectors
from .models import Attribute, Category, Collection, Product, ProductVariant
from .serializers import (
    AttributeSerializer,
    CategorySerializer,
    CollectionSerializer,
    MediaSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductVariantSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    serializer_class = CategorySerializer
    lookup_field = "slug"

    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, slug=None):
        qs = selectors.list_products_in_category(category_slug=slug)
        return Response(ProductListSerializer(qs, many=True).data)


CategoryViewSet = extend_schema_view(
    list=extend_schema(
        summary="List categories",
        description="Returns active categories ordered by sort_order then name",
        tags=["Catalog"],
        examples=[
            OpenApiExample(
                "Category list",
                value={
                    "count": 3,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "name": "Audio",
                            "slug": "audio",
                            "description": "Audio equipment",
                            "parent": None,
                            "is_active": True,
                            "sort_order": 0,
                        }
                    ],
                },
                response_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Get category by slug",
        description="Returns a single category by its slug",
        tags=["Catalog"],
        examples=[
            OpenApiExample(
                "Category detail",
                value={
                    "id": 1,
                    "name": "Audio",
                    "slug": "audio",
                    "description": "Audio equipment",
                    "parent": None,
                    "is_active": True,
                    "sort_order": 0,
                },
                response_only=True,
            )
        ],
    ),
)(CategoryViewSet)


class ProductFilterSet(filters.FilterSet):
    category = filters.CharFilter(field_name="categories__slug")
    status = filters.CharFilter(field_name="status")

    class Meta:
        model = Product
        fields = ["category", "status"]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"
    filterset_class = ProductFilterSet

    # Support both `search` and `q` query params for search
    class QSearchFilter(drf_filters.SearchFilter):
        search_param = "q"

    filter_backends = [
        filters.DjangoFilterBackend,
        drf_filters.OrderingFilter,
        drf_filters.SearchFilter,
        QSearchFilter,
    ]
    ordering_fields = ["title", "created_at"]
    search_fields = ["title", "description", "categories__name"]

    def get_queryset(self):
        # Use selectors for list; prefetch full relations for detail.
        if self.action == "list":
            # Filtering/search is applied by DRF backends; selectors provide optimized prefetch for list.
            return selectors.list_products()
        return Product.objects.all().prefetch_related("media", "categories").order_by("title")

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer

    @action(detail=True, methods=["get"], url_path="variants")
    def variants(self, request, slug=None):
        product = selectors.get_product_by_slug(slug)
        if not product or product.status != Product.STATUS_PUBLISHED:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        qs = selectors.list_variants_by_product_slug(product_slug=slug).filter(status=ProductVariant.STATUS_ACTIVE)
        return Response(ProductVariantSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="media")
    def media(self, request, slug=None):
        product = selectors.get_product_by_slug(slug)
        if not product or product.status != Product.STATUS_PUBLISHED:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        qs = selectors.list_media_by_product_slug(product_slug=slug)
        return Response(MediaSerializer(qs, many=True).data)


ProductViewSet = extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Returns products with filtering, search, ordering, and pagination",
        tags=["Catalog"],
        parameters=[
            OpenApiParameter("category", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Category slug"),
            OpenApiParameter("status", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Product status"),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Ordering field (e.g., title, -created_at)",
            ),
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Search in title/description",
            ),
        ],
        examples=[
            OpenApiExample(
                "Product list",
                value={
                    "count": 2,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "Studio Monitor Speakers",
                            "slug": "studio-monitor-speakers",
                            "primary_media_url": "https://images.example.com/monitor-speakers-primary.jpg",
                            "primary_category": {"name": "Audio", "slug": "audio"},
                        }
                    ],
                },
                response_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Get product by slug",
        description="Returns a single product with categories and media",
        tags=["Catalog"],
        examples=[
            OpenApiExample(
                "Product detail",
                value={
                    "id": 1,
                    "title": "Studio Monitor Speakers",
                    "slug": "studio-monitor-speakers",
                    "description": "High-fidelity nearfield monitors for accurate mixing.",
                    "status": "published",
                    "seo_title": "Studio Monitor Speakers",
                    "seo_description": "Nearfield monitors",
                    "categories": [
                        {
                            "id": 1,
                            "name": "Audio",
                            "slug": "audio",
                            "description": "Audio equipment",
                            "parent": None,
                            "is_active": True,
                            "sort_order": 0,
                        }
                    ],
                    "media": [
                        {
                            "id": 10,
                            "url": "https://images.example.com/monitor-speakers-primary.jpg",
                            "alt_text": "Studio monitor speakers",
                            "is_primary": True,
                            "sort_order": 0,
                        }
                    ],
                },
                response_only=True,
            )
        ],
    ),
)(ProductViewSet)


class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Collection.objects.filter(is_active=True).order_by("sort_order", "name")
    serializer_class = CollectionSerializer
    lookup_field = "slug"

    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, slug=None):
        qs = selectors.list_collection_products(collection_slug=slug)
        return Response(ProductListSerializer(qs, many=True).data)


CollectionViewSet = extend_schema_view(
    list=extend_schema(
        summary="List collections",
        description=(
            "Returns active collections ordered by sort_order then name.\n\n"
            "Ordering of products within a collection is curated via the CollectionProduct through model."
        ),
        tags=["Catalog"],
        examples=[
            OpenApiExample(
                "Collection list",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "name": "Featured",
                            "slug": "featured",
                            "description": "Featured products",
                            "is_active": True,
                            "sort_order": 0,
                        }
                    ],
                },
                response_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Get collection by slug",
        description=(
            "Returns a single collection by its slug.\n\n"
            "Products associated with a collection are presented in the curated order defined by CollectionProduct."
        ),
        tags=["Catalog"],
        examples=[
            OpenApiExample(
                "Collection detail",
                value={
                    "id": 1,
                    "name": "Featured",
                    "slug": "featured",
                    "description": "Featured products",
                    "is_active": True,
                    "sort_order": 0,
                },
                response_only=True,
            )
        ],
    ),
)(CollectionViewSet)


class VariantFilterSet(filters.FilterSet):
    product = filters.CharFilter(field_name="product__slug")
    status = filters.CharFilter(field_name="status")

    class Meta:
        model = ProductVariant
        fields = ["product", "status"]


class VariantViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductVariantSerializer
    filterset_class = VariantFilterSet
    filter_backends = [filters.DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter]
    ordering_fields = ["sku", "id"]
    search_fields = ["sku", "barcode"]

    def get_queryset(self):
        qs = ProductVariant.objects.select_related("product").order_by("sku")
        # Enforce product visibility: only variants of published products in public API
        qs = qs.filter(product__status=Product.STATUS_PUBLISHED)
        # Annotate availability from inventory.StockItem
        qty_sub = Subquery(StockItem.objects.filter(variant_id=OuterRef("pk")).values("quantity")[:1])
        res_sub = Subquery(StockItem.objects.filter(variant_id=OuterRef("pk")).values("reserved")[:1])
        return qs.annotate(available=Coalesce(qty_sub, 0) - Coalesce(res_sub, 0))


VariantViewSet = extend_schema_view(
    list=extend_schema(summary="List variants", tags=["Catalog"]),
    retrieve=extend_schema(summary="Get variant by id", tags=["Catalog"]),
)(VariantViewSet)


class AttributeFilterSet(filters.FilterSet):
    is_filterable = filters.BooleanFilter(field_name="is_filterable")

    class Meta:
        model = Attribute
        fields = ["is_filterable"]


class AttributeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attribute.objects.order_by("sort_order", "name")
    serializer_class = AttributeSerializer
    filterset_class = AttributeFilterSet
    filter_backends = [filters.DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter]
    ordering_fields = ["name", "sort_order"]
    search_fields = ["name", "code"]


AttributeViewSet = extend_schema_view(
    list=extend_schema(summary="List attributes", tags=["Catalog"]),
    retrieve=extend_schema(summary="Get attribute by id", tags=["Catalog"]),
)(AttributeViewSet)
