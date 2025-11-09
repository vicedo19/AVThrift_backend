from django.urls import path

from .views import InventoryHealthView, InventoryRoadmapView

urlpatterns = [
    path("health/", InventoryHealthView.as_view(), name="inventory-health"),
    path("", InventoryRoadmapView.as_view(), name="inventory-roadmap"),
]

# EOF
