"""Carrier authentication and network allow-listing."""
import hashlib
import hmac
import ipaddress


def carrier_authorized(depot, carrier, token):
    entry = depot.carriers.get(carrier)
    if entry is None:
        return False
    return hmac.compare_digest(entry["token"], token)


def ip_allowed(depot, ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in depot.allowed_nets)


def signature_ok(body, signature, key):
    if not signature:
        return False
    expect = hmac.new(key.encode(), body.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expect, signature)
