"""Cart services: mutations with inventory reservations."""

from decimal import Decimal

from catalog.models import ProductVariant
from django.db import transaction
from django.shortcuts import get_object_or_404
from inventory.services import convert_reservation_to_order, create_reservation, release_reservation

from .models import Cart, CartItem
from .selectors import get_active_cart_for_user


class CartError(Exception):
    """Raised for cart mutation failures."""


@transaction.atomic
def add_item(*, user, variant_id: int, quantity: int) -> CartItem:
    """Add a variant to the user's cart, creating or updating the line item.

    Reserves inventory equal to the desired quantity.
    """

    if quantity <= 0:
        raise CartError("Quantity must be positive")
    cart = get_active_cart_for_user(user=user)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    try:
        item = CartItem.objects.select_for_update().get(cart=cart, variant=variant)
        # Re-reserve to match new quantity
        if item.reservation_id:
            release_reservation(reservation_id=item.reservation_id)
        reservation = create_reservation(
            variant_id=variant.id,
            quantity=quantity,
            reference=f"cart:{cart.id}",
        )
        # Safety: reservation must match the variant being added
        if reservation.variant_id != variant.id:
            release_reservation(reservation_id=reservation.id)
            raise CartError("Reservation variant mismatch")
        item.quantity = quantity
        item.unit_price = variant.price or Decimal("0.00")
        item.reservation = reservation
        item.save(update_fields=["quantity", "unit_price", "reservation", "updated_at"])
        return item
    except CartItem.DoesNotExist:
        reservation = create_reservation(
            variant_id=variant.id,
            quantity=quantity,
            reference=f"cart:{cart.id}",
        )
        if reservation.variant_id != variant.id:
            release_reservation(reservation_id=reservation.id)
            raise CartError("Reservation variant mismatch")
        return CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=quantity,
            unit_price=variant.price or Decimal("0.00"),
            reservation=reservation,
        )


@transaction.atomic
def update_item_quantity(*, user, item_id: int, quantity: int) -> CartItem:
    """Update a cart item's quantity, re-syncing reservations."""

    if quantity <= 0:
        raise CartError("Quantity must be positive")
    cart = get_active_cart_for_user(user=user)
    item = get_object_or_404(CartItem.objects.select_for_update(), id=item_id, cart=cart)

    # Replace reservation with the new quantity
    if item.reservation_id:
        release_reservation(reservation_id=item.reservation_id)
    reservation = create_reservation(
        variant_id=item.variant_id,
        quantity=quantity,
        reference=f"cart:{cart.id}",
    )
    if reservation.variant_id != item.variant_id:
        release_reservation(reservation_id=reservation.id)
        raise CartError("Reservation variant mismatch")
    item.quantity = quantity
    item.unit_price = item.variant.price or Decimal("0.00")
    item.reservation = reservation
    item.save(update_fields=["quantity", "unit_price", "reservation", "updated_at"])
    return item


@transaction.atomic
def remove_item(*, user, item_id: int) -> None:
    """Remove an item from the cart and release its reservation."""

    cart = get_active_cart_for_user(user=user)
    try:
        item = CartItem.objects.select_for_update().get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return
    if item.reservation_id:
        release_reservation(reservation_id=item.reservation_id)
    item.delete()


@transaction.atomic
def clear_cart(*, user) -> None:
    """Clear the user's cart and release all reservations."""

    cart = get_active_cart_for_user(user=user)
    for item in CartItem.objects.select_for_update().filter(cart=cart):
        if item.reservation_id:
            release_reservation(reservation_id=item.reservation_id)
    CartItem.objects.filter(cart=cart).delete()


@transaction.atomic
def checkout_cart(*, user) -> None:
    """Checkout the active cart: convert reservations and mark as ordered.

    Converts each active reservation to an order movement, clears items,
    and transitions cart status to ordered.
    """

    cart = get_active_cart_for_user(user=user)
    # Convert all active reservations to orders
    for item in CartItem.objects.select_for_update().filter(cart=cart):
        if item.reservation_id:
            convert_reservation_to_order(
                reservation_id=item.reservation_id,
                reason="cart checkout",
                reference=f"cart:{cart.id}",
            )
    # Clear items after conversion
    CartItem.objects.filter(cart=cart).delete()
    cart.status = Cart.STATUS_ORDERED
    cart.save(update_fields=["status", "updated_at"])


@transaction.atomic
def abandon_cart(*, user) -> None:
    """Abandon the active cart: release reservations and mark as abandoned."""

    cart = get_active_cart_for_user(user=user)
    for item in CartItem.objects.select_for_update().filter(cart=cart):
        if item.reservation_id:
            release_reservation(reservation_id=item.reservation_id)
    CartItem.objects.filter(cart=cart).delete()
    cart.status = Cart.STATUS_ABANDONED
    cart.save(update_fields=["status", "updated_at"])
