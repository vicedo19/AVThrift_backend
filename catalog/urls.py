"""URL routes for the catalog app."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet, CollectionViewSet, ProductViewSet

router = SimpleRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"collections", CollectionViewSet, basename="collection")

urlpatterns = [path("", include(router.urls))]
