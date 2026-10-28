"""Parsing of parcel fields from requests."""
MAX_GRAMS = 30000
SERVICES = ("ground", "air", "freight")


def parse_weight(text):
    grams = int(text)
    if grams <= 0:
        raise ValueError("weight must be positive")
    if grams > MAX_GRAMS:
        raise ValueError("too heavy")
    return grams


def parse_zip(code):
    code = code.strip()
    if not (len(code) == 5 and code.isdigit()):
        raise ValueError("bad zip")
    return code


def parse_service(name):
    name = name.lower()
    if name not in SERVICES:
        raise ValueError("unknown service")
    return name
