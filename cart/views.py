"""DRF views for cart operations."""

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from inventory.services import MovementError
from rest_framework import serializers as rf_serializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartItem
from .selectors import get_active_cart_for_user
from .serializers import AddItemSerializer, CartReadSerializer, UpdateItemQuantitySerializer
from .services import CartError, abandon_cart, checkout_cart, clear_cart, remove_item


class CartDetailView(APIView):
    """Return the authenticated user's active cart."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Get active cart",
        description="Returns the authenticated user's active cart including items and totals.",
        examples=[
            OpenApiExample(
                "Cart",
                value={
                    "id": 1,
                    "items": [
                        {
                            "id": 10,
                            "variant_id": 100,
                            "quantity": 2,
                            "unit_price": "4999.00",
                            "line_total": "9998.00",
                        }
                    ],
                    "subtotal": "9998.00",
                    "total": "9998.00",
                },
            )
        ],
    )
    def get(self, request):
        cart = get_active_cart_for_user(user=request.user)
        data = CartReadSerializer.from_cart(cart=cart).data
        return Response(data, status=status.HTTP_200_OK)


class CartAddItemView(APIView):
    """Add an item to the cart."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart_write"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Add item to cart",
        description="Adds a product variant to the user's cart and reserves stock.",
        request=AddItemSerializer,
        responses={
            201: inline_serializer(
                name="CartItemCreatedResponse",
                fields={"id": rf_serializers.IntegerField()},
            ),
            400: inline_serializer(name="CartMutationError", fields={"detail": rf_serializers.CharField()}),
            404: inline_serializer(name="NotFoundError", fields={"detail": rf_serializers.CharField()}),
        },
        examples=[OpenApiExample("Added", value={"id": 10})],
    )
    def post(self, request):
        serializer = AddItemSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            item = serializer.save()
            return Response({"id": item.id}, status=status.HTTP_201_CREATED)
        except (MovementError, CartError):
            # Generic error response for reservation or cart failures
            return Response({"detail": "Unable to update cart."}, status=status.HTTP_400_BAD_REQUEST)


class CartItemUpdateView(APIView):
    """Update a cart item's quantity."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart_write"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Update cart item quantity",
        description="Updates quantity and re-syncs reservation for a cart item.",
        request=UpdateItemQuantitySerializer,
        responses={
            200: inline_serializer(
                name="CartItemUpdatedResponse",
                fields={"id": rf_serializers.IntegerField()},
            ),
            400: inline_serializer(name="CartMutationError", fields={"detail": rf_serializers.CharField()}),
            404: inline_serializer(name="NotFoundError", fields={"detail": rf_serializers.CharField()}),
        },
        examples=[OpenApiExample("Updated", value={"id": 10})],
    )
    def patch(self, request, item_id: int):
        try:
            item = CartItem.objects.get(id=item_id, cart__user_id=request.user.id)
        except CartItem.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateItemQuantitySerializer(instance=item, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
            return Response({"id": item.id}, status=status.HTTP_200_OK)
        except (MovementError, CartError):
            return Response({"detail": "Unable to update cart."}, status=status.HTTP_400_BAD_REQUEST)


class CartItemDeleteView(APIView):
    """Remove an item from the cart."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart_write"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Delete cart item",
        description="Removes a cart item and releases its reservation.",
        responses={
            204: None,
            404: inline_serializer(name="NotFoundError", fields={"detail": rf_serializers.CharField()}),
        },
        examples=[OpenApiExample("No Content", value=None)],
    )
    def delete(self, request, item_id: int):
        # Ensure item belongs to the authenticated user; otherwise return 404
        if not CartItem.objects.filter(id=item_id, cart__user_id=request.user.id).exists():
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        remove_item(user=request.user, item_id=item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartCheckoutView(APIView):
    """Checkout the active cart and mark it ordered."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart_write"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Checkout cart",
        description="Converts reservations to orders and marks the active cart as ordered.",
        responses={
            200: inline_serializer(name="CartStatusOrdered", fields={"status": rf_serializers.CharField()}),
            400: inline_serializer(name="CartMutationError", fields={"detail": rf_serializers.CharField()}),
        },
        examples=[
            OpenApiExample("Ordered", value={"status": "ordered"}),
            OpenApiExample("Mutation Error", value={"detail": "Unable to update cart."}),
        ],
    )
    def post(self, request):
        checkout_cart(user=request.user)
        return Response({"status": "ordered"}, status=status.HTTP_200_OK)


class CartAbandonView(APIView):
    """Abandon the active cart and release reservations."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart_write"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Abandon cart",
        description="Releases reservations and marks the active cart as abandoned.",
        responses={
            200: inline_serializer(name="CartStatusAbandoned", fields={"status": rf_serializers.CharField()}),
            400: inline_serializer(name="CartMutationError", fields={"detail": rf_serializers.CharField()}),
        },
        examples=[
            OpenApiExample("Abandoned", value={"status": "abandoned"}),
            OpenApiExample("Mutation Error", value={"detail": "Unable to update cart."}),
        ],
    )
    def post(self, request):
        abandon_cart(user=request.user)
        return Response({"status": "abandoned"}, status=status.HTTP_200_OK)


class CartClearView(APIView):
    """Clear the active cart: delete items and release reservations."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "cart_write"

    @extend_schema(
        tags=["Cart Endpoints"],
        summary="Clear cart",
        description="Deletes items and releases any active reservations in the cart.",
        responses={
            200: inline_serializer(name="CartStatusCleared", fields={"status": rf_serializers.CharField()}),
            400: inline_serializer(name="CartMutationError", fields={"detail": rf_serializers.CharField()}),
        },
        examples=[
            OpenApiExample("Cleared", value={"status": "cleared"}),
            OpenApiExample("Mutation Error", value={"detail": "Unable to update cart."}),
        ],
    )
    def post(self, request):
        clear_cart(user=request.user)
        return Response({"status": "cleared"}, status=status.HTTP_200_OK)
