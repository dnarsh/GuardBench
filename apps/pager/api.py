"""List endpoint."""
from db import ConnectError
from paginate import has_next, page_count, page_slice, validate_args
from search import names, search


def list_items(db, term="", page=1, size=20):
    """Return (status, body): 200 with a page of names, 400 for bad input, 503 when the db is down."""
    try:
        page, size = validate_args(page, size)
        found = search(db.connect().rows, term)
    except ValueError as e:
        return 400, {"error": str(e)}
    except ConnectError as e:
        return 503, {"error": str(e)}
    return 200, {
        "items": names(page_slice(found, page, size)),
        "page": page,
        "pages": page_count(len(found), size),
        "next": has_next(len(found), page, size),
    }
