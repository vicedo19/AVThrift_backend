import pytest
from cart.services import add_item, update_item_quantity
from cart.tests.factories import StockItemFactory, UserFactory
from catalog.tests.factories import ProductVariantFactory
from inventory.models import StockItem, StockReservation
from inventory.services import MovementError


@pytest.mark.django_db
def test_rapid_quantity_updates_syncs_to_latest_reservation():
    user = UserFactory()
    variant = ProductVariantFactory()
    StockItemFactory(variant=variant, quantity=10, reserved=0)

    # Start with quantity=1
    item = add_item(user=user, variant_id=variant.id, quantity=1)
    # Rapid updates to different quantities
    update_item_quantity(user=user, item_id=item.id, quantity=2)
    update_item_quantity(user=user, item_id=item.id, quantity=5)
    item = update_item_quantity(user=user, item_id=item.id, quantity=3)

    # Final reservation should reflect latest quantity
    stock_item = StockItem.objects.get(variant_id=variant.id)
    assert stock_item.reserved == 3

    # Only one active reservation should remain for the variant
    active = list(StockReservation.objects.filter(variant_id=variant.id, state=StockReservation.STATE_ACTIVE))
    assert len(active) == 1
    assert active[0].quantity == 3


@pytest.mark.django_db
def test_competing_reservations_two_users_exceeds_available():
    user1 = UserFactory()
    user2 = UserFactory()
    variant = ProductVariantFactory()
    # Only 5 available
    StockItemFactory(variant=variant, quantity=5, reserved=0)

    # First user reserves 3 successfully
    item1 = add_item(user=user1, variant_id=variant.id, quantity=3)
    stock_item = StockItem.objects.get(variant_id=variant.id)
    assert stock_item.reserved == 3

    # Second user attempts to reserve 3 (would exceed available=2 -> 3)
    with pytest.raises(MovementError):
        add_item(user=user2, variant_id=variant.id, quantity=3)

    stock_item.refresh_from_db()
    assert stock_item.reserved == 3

    # Only one active reservation exists
    active = list(StockReservation.objects.filter(variant_id=variant.id, state=StockReservation.STATE_ACTIVE))
    assert len(active) == 1
    assert active[0].quantity == 3
    assert active[0].id == item1.reservation_id


@pytest.mark.django_db
def test_update_failure_leaves_consistent_state_and_allows_future_updates():
    user = UserFactory()
    variant = ProductVariantFactory()
    # Make 3 available, reserve 2 via add_item
    StockItemFactory(variant=variant, quantity=3, reserved=0)
    item = add_item(user=user, variant_id=variant.id, quantity=2)

    # Attempt to update to 5 -> should fail; previous reservation should remain due to atomic rollback
    with pytest.raises(MovementError):
        update_item_quantity(user=user, item_id=item.id, quantity=5)

    stock_item = StockItem.objects.get(variant_id=variant.id)
    assert stock_item.reserved == 2  # unchanged because the whole transaction rolled back

    # The item's reservation record should still be active
    res = StockReservation.objects.get(id=item.reservation_id)
    assert res.state == StockReservation.STATE_ACTIVE

    # Future update within availability should succeed and create a new active reservation
    item = update_item_quantity(user=user, item_id=item.id, quantity=1)
    stock_item.refresh_from_db()
    assert stock_item.reserved == 1
    res2 = StockReservation.objects.get(id=item.reservation_id)
    assert res2.state == StockReservation.STATE_ACTIVE
