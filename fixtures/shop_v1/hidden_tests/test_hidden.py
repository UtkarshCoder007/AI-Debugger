import pytest

from shop.inventory import Inventory, OutOfStockError
from shop.orders import place_order
from shop.pricing import line_total
from shop.report import average_order_value, paginate


def make_inventory():
    inv = Inventory()
    inv.add_item("pen", 2.0, 100)
    inv.add_item("book", 10.0, 3)
    return inv


class TestRemoveStock:
    def test_removing_exact_stock_succeeds(self):
        inv = make_inventory()
        inv.remove_stock("book", 3)
        assert inv.get_qty("book") == 0

    def test_removing_all_but_one(self):
        inv = make_inventory()
        inv.remove_stock("book", 2)
        assert inv.get_qty("book") == 1

    def test_removing_more_than_stock_raises_and_changes_nothing(self):
        inv = make_inventory()
        with pytest.raises(OutOfStockError):
            inv.remove_stock("book", 4)
        assert inv.get_qty("book") == 3

    def test_order_for_exact_stock_goes_through(self):
        inv = make_inventory()
        assert place_order(inv, [("book", 3)]) == 30.0
        assert inv.get_qty("book") == 0


class TestBulkDiscount:
    @pytest.mark.parametrize("qty, expected", [(10, 10.0), (11, 9.9), (50, 45.0), (51, 40.8), (60, 48.0)])
    def test_line_total_tiers(self, qty, expected):
        assert line_total(1.0, qty) == pytest.approx(expected)


class TestAtomicOrder:
    def test_failed_order_leaves_all_stock_untouched(self):
        inv = make_inventory()
        with pytest.raises(OutOfStockError):
            place_order(inv, [("pen", 5), ("book", 10)])
        assert inv.get_qty("pen") == 100
        assert inv.get_qty("book") == 3

    def test_failing_first_item_changes_nothing(self):
        inv = make_inventory()
        with pytest.raises(OutOfStockError):
            place_order(inv, [("book", 10), ("pen", 5)])
        assert inv.get_qty("pen") == 100

    def test_successful_order_deducts_stock_and_totals(self):
        inv = make_inventory()
        assert place_order(inv, [("pen", 5), ("book", 2)]) == 30.0
        assert inv.get_qty("pen") == 95
        assert inv.get_qty("book") == 1


ITEMS = list(range(1, 11))


class TestPagination:
    def test_first_page(self):
        assert paginate(ITEMS, 1, 3) == [1, 2, 3]

    def test_second_page(self):
        assert paginate(ITEMS, 2, 3) == [4, 5, 6]

    def test_partial_last_page(self):
        assert paginate(ITEMS, 4, 3) == [10]

    def test_page_past_the_end_is_empty(self):
        assert paginate(ITEMS, 5, 3) == []


class TestAverageOrderValue:
    def test_average_of_values(self):
        assert average_order_value([10, 20, 30]) == pytest.approx(20)

    def test_empty_list_does_not_divide_by_zero(self):
        # The code never says what an empty list should return, so any non-crashing
        # behaviour is accepted: a number, None, or a clear ValueError.
        try:
            result = average_order_value([])
        except ZeroDivisionError:
            pytest.fail("average_order_value([]) raised ZeroDivisionError")
        except ValueError:
            return
        assert result is None or isinstance(result, (int, float))