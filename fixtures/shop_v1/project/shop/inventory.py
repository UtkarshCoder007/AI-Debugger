class OutOfStockError(Exception):
    pass


class Inventory:
    def __init__(self):
        self._items = {}  # name -> {"price": float, "qty": int}

    def add_item(self, name, price, qty):
        if price < 0 or qty < 0:
            raise ValueError("price and qty must be non-negative")
        if name in self._items:
            self._items[name]["qty"] += qty
        else:
            self._items[name] = {"price": price, "qty": qty}

    def get_price(self, name):
        return self._items[name]["price"]

    def get_qty(self, name):
        return self._items[name]["qty"]

    def remove_stock(self, name, qty):
        if self._items[name]["qty"] <= qty:
            raise OutOfStockError(name)
        self._items[name]["qty"] -= qty

    def low_stock(self, threshold=5):
        return sorted(n for n, i in self._items.items() if i["qty"] < threshold)