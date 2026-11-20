def bulk_discount_rate(qty):
    if qty > 10:
        return 0.10
    elif qty > 50:
        return 0.20
    return 0.0


def line_total(unit_price, qty):
    rate = bulk_discount_rate(qty)
    return round(unit_price * qty * (1 - rate), 2)