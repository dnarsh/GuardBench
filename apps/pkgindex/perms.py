"""Who may publish and which API keys are good."""
import hmac


def may_publish(index, user, pkg):
    owners = index.owners.get(pkg)
    if owners is None:
        return False
    return user in owners


def api_key_valid(index, user, key):
    try:
        stored = index.api_keys[user]
    except KeyError:
        return False
    return hmac.compare_digest(stored, key)


def is_owner_of_any(index, user):
    return any(user in owners for owners in index.owners.values())
