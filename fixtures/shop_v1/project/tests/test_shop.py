import pytest
from shop.inventory import Inventory, OutOfStockError
from shop.pricing import line_total
from shop.orders import place_order


def make_inventory():
    inv = Inventory()
    inv.add_item("pen", 2.0, 100)
    inv.add_item("book", 10.0, 3)
    return inv


def test_add_item_accumulates_quantity():
    inv = make_inventory()
    inv.add_item("pen", 2.0, 20)
    assert inv.get_qty("pen") == 120


def test_add_item_rejects_negative_values():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.add_item("pen", -1, 5)


def test_remove_stock_partial():
    inv = make_inventory()
    inv.remove_stock("pen", 30)
    assert inv.get_qty("pen") == 70


def test_remove_stock_exact_amount():
    inv = make_inventory()
    inv.remove_stock("book", 3)
    assert inv.get_qty("book") == 0


def test_remove_stock_too_much_raises():
    inv = make_inventory()
    with pytest.raises(OutOfStockError):
        inv.remove_stock("book", 4)


def test_low_stock_is_sorted():
    inv = make_inventory()
    inv.add_item("ant", 1.0, 1)
    assert inv.low_stock() == ["ant", "book"]


def test_line_total_no_discount():
    assert line_total(2.0, 5) == 10.0


def test_line_total_ten_percent():
    assert line_total(2.0, 20) == 36.0


def test_line_total_twenty_percent():
    assert line_total(2.0, 60) == 96.0


def test_place_order_success():
    inv = make_inventory()
    assert place_order(inv, [("pen", 5), ("book", 2)]) == 30.0