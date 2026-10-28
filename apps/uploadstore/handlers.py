"""HTTP-ish handlers returning (status, body)."""
from quota import QuotaError


def upload(store, name, data):
    try:
        store.save(name, data)
    except QuotaError as e:
        return 413, str(e)
    except ValueError as e:
        return 400, str(e)
    return 201, "saved"


def download(store, name):
    try:
        return 200, store.load(name)
    except ValueError as e:
        return 400, str(e)
    except FileNotFoundError:
        return 404, "not found"


def listing(store):
    """(200, stored names joined by newlines)."""
    return 200, "\n".join(store.names())


def remove(store, name):
    try:
        store.delete(name)
    except ValueError as e:
        return 400, str(e)
    except FileNotFoundError:
        return 404, "not found"
    return 204, ""
