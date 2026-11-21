def paginate(items, page, page_size):
    """Return the items on the given page. Pages are 1-based."""
    start = (page - 1) * page_size
    return items[start:start + page_size]


def average_order_value(totals):
    if not totals:
        return 0.0
    return sum(totals) / len(totals)