"""Read-only viewsets for catalog resources (initial MVP)."""

from django.db.models import Prefetch
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters as drf_filters
from rest_framework import viewsets

from .models import Category, Collection, Media, Product
from .serializers import CategorySerializer, CollectionSerializer, ProductDetailSerializer, ProductListSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    serializer_class = CategorySerializer
    lookup_field = "slug"


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
    price_min = filters.NumberFilter(field_name="default_price", lookup_expr="gte")
    price_max = filters.NumberFilter(field_name="default_price", lookup_expr="lte")
    category = filters.CharFilter(field_name="categories__slug")
    status = filters.CharFilter(field_name="status")
    currency = filters.CharFilter(field_name="currency")

    class Meta:
        model = Product
        fields = ["category", "status", "currency", "price_min", "price_max"]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "slug"
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
    ordering_fields = ["title", "default_price", "created_at"]
    search_fields = ["title", "description", "categories__name"]

    def get_queryset(self):
        # Selective prefetch: only primary media on list, full media on detail
        if self.action == "list":
            qs = (
                Product.objects.all()
                .prefetch_related(
                    Prefetch("media", queryset=Media.objects.filter(is_primary=True)),
                    "categories",
                )
                .order_by("title")
            )
        else:
            qs = Product.objects.all().prefetch_related("media", "categories").order_by("title")
        return qs

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer


ProductViewSet = extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="Returns products with filtering, search, ordering, and pagination",
        tags=["Catalog"],
        parameters=[
            OpenApiParameter("category", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Category slug"),
            OpenApiParameter("status", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Product status"),
            OpenApiParameter(
                "currency", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Currency code (e.g., NGN)"
            ),
            OpenApiParameter("price_min", OpenApiTypes.NUMBER, OpenApiParameter.QUERY, description="Minimum price"),
            OpenApiParameter("price_max", OpenApiTypes.NUMBER, OpenApiParameter.QUERY, description="Maximum price"),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Ordering field (e.g., title, -created_at, default_price)",
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
                            "default_price": "299.99",
                            "currency": "NGN",
                            "primary_media_url": "https://images.example.com/monitor-speakers-primary.jpg",
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
                    "default_price": "299.99",
                    "currency": "NGN",
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


CollectionViewSet = extend_schema_view(
    list=extend_schema(
        summary="List collections",
        description="Returns active collections ordered by sort_order then name",
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
        description="Returns a single collection by its slug",
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
