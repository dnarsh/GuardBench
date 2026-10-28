"""Who may do what on the desk."""
import hmac


def authenticate(desk, name, key):
    expected = desk.api_keys.get(name)
    if expected is None:
        return False
    return hmac.compare_digest(expected, key)


def can_close(desk, name, ticket):
    try:
        role = desk.agents[name]
    except KeyError:
        return False
    if role == "admin":
        return True
    return role == "agent" and ticket["assignee"] == name


def can_view(desk, name, ticket):
    role = desk.agents.get(name)
    if role is None:
        return name == ticket["author"]
    return True
