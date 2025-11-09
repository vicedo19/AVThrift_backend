"""Serializers for the catalog app (read-only initial MVP)."""

from rest_framework import serializers

from .models import Category, Collection, Media, Product


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ["id", "url", "alt_text", "is_primary", "sort_order"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "parent", "is_active", "sort_order"]


class ProductListSerializer(serializers.ModelSerializer):
    primary_media_url = serializers.SerializerMethodField()
    primary_category = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "primary_media_url",
            "primary_category",
        ]

    def get_primary_media_url(self, obj):
        media = getattr(obj, "_prefetched_objects_cache", {}).get("media")
        items = list(media) if media is not None else list(obj.media.all())
        primary = next((m for m in items if m.is_primary), None)
        return primary.url if primary else None

    def get_primary_category(self, obj):
        cats = getattr(obj, "_prefetched_objects_cache", {}).get("categories")
        items = list(cats) if cats is not None else list(obj.categories.all())
        if not items:
            return None
        c = items[0]
        return {"name": c.name, "slug": c.slug}


class ProductDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True)
    media = MediaSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "status",
            "seo_title",
            "seo_description",
            "categories",
            "media",
        ]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "name", "slug", "description", "is_active", "sort_order"]


# Variant serializer will remain in views layer if needed; inventory overlay removed.
