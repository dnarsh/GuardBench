"""Digest text and operator rows; unsubscribe tokens and URL query strings stay out."""


def subscriber_row(user, record):
    return {"user": user, "feeds": len(record["feeds"])}


def fetch_error(url, err):
    return "could not fetch %s: %s" % (url.split("?")[0], err)


def item_line(item):
    return "- %s (%s)" % (item["title"], item["feed"])
