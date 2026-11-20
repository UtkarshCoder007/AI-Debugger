from .pricing import line_total


def place_order(inventory, items):
    """items is a list of (name, qty). Returns the order total.
    The order is all-or-nothing: if any item fails, stock is unchanged."""
    total = 0.0
    for name, qty in items:
        inventory.remove_stock(name, qty)
        total += line_total(inventory.get_price(name), qty)
    return round(total, 2)