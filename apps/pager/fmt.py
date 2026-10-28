"""Text for list pages."""


def page_label(page, pages):
    """'page 2 of 5'; 'no results' when there are no pages."""
    if pages == 0:
        return "no results"
    return "page %d of %d" % (page, pages)


def range_label(page, size, total):
    """'21-40 of 95' for the items shown on the page."""
    first = (page - 1) * size + 1
    last = min(page * size, total)
    if total == 0 or first > total:
        return "0 of %d" % total
    return "%d-%d of %d" % (first, last, total)
