"""Filtering and ordering before pagination."""

ALLOWED_SORT = ("name", "price")


def matches(item, term):
    """Case-insensitive substring match on the item name; an empty term matches everything."""
    return term.lower() in item["name"].lower()


def search(items, term="", sort_key="name", descending=False):
    """Filtered copy of items ordered by sort_key."""
    if sort_key not in ALLOWED_SORT:
        raise ValueError("cannot sort by %r" % sort_key)
    found = [item for item in items if matches(item, term)]
    found.sort(key=lambda item: item[sort_key], reverse=descending)
    return found


def names(items):
    """Just the names, in order."""
    return [item["name"] for item in items]
