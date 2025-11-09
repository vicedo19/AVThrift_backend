"""Inventory health and scaffold views."""

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class InventoryHealthView(APIView):
    throttle_classes = []

    @extend_schema(
        tags=["Inventory"],
        summary="Inventory health",
        description="Simple healthcheck endpoint for the inventory app",
        examples=[OpenApiExample("Health OK", value={"status": "ok", "app": "inventory"})],
    )
    def get(self, request):
        return Response({"status": "ok", "app": "inventory"})


class InventoryRoadmapView(APIView):
    throttle_classes = []

    @extend_schema(
        tags=["Inventory"],
        summary="Inventory API scaffold",
        description="Placeholder endpoint describing upcoming inventory resources and endpoints.",
    )
    def get(self, request):
        return Response(
            {
                "endpoints": [
                    {"path": "/api/v1/inventory/stock-items/", "status": "planned"},
                    {"path": "/api/v1/inventory/movements/", "status": "planned"},
                ]
            }
        )


# EOF
