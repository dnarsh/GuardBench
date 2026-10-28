"""Text and dict views of desk data."""


def agent_summary(desk, name):
    return {"name": name, "role": desk.agents[name]}


def login_failed(name, key):
    return "login failed for %s" % name


def ticket_line(ticket):
    return "#%d [%s] %s" % (ticket["id"], ticket["priority"], ticket["title"])
