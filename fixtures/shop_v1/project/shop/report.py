def paginate(items, page, page_size):
    """Return the items on the given page. Pages are 1-based."""
    start = page * page_size
    return items[start:start + page_size]


def average_order_value(totals):
    return sum(totals) / len(totals)