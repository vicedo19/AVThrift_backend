"""Admin registration for catalog models."""

from django.contrib import admin

from .models import Category, Collection, Media, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "sort_order")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


class MediaInline(admin.TabularInline):
    model = Media
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "default_price", "currency")
    list_editable = ("currency",)
    search_fields = ("title", "slug")
    list_filter = ("status", "categories")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [MediaInline]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "sku", "status", "price", "currency")
    list_editable = ("currency",)
    search_fields = ("sku",)
    list_filter = ("status",)
