"""Plans and validation of sizes."""
PLANS = ("free", "pro", "team")
FEATURES = {"free": ("share",), "pro": ("share", "export"), "team": ("share", "export", "audit")}


def cheapest_with(feature):
    for plan in PLANS:
        if feature in FEATURES[plan]:
            return plan
    return None


def check_plan(name):
    if name not in PLANS:
        raise ValueError("unknown plan")
    return name


def check_bytes(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("size must be a non-negative integer")
    return n
