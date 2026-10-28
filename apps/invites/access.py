"""Who may invite, and which codes and addresses are acceptable."""


def verify_code(ws, code):
    invite = ws.invites.get(code)
    if invite is None:
        return False
    return not invite["used"]


def may_invite(ws, actor):
    try:
        role = ws.members[actor]["role"]
    except KeyError:
        return False
    return role in ("owner", "admin")


def domain_ok(ws, email):
    try:
        domain = email.rsplit("@", 1)[1].lower()
    except IndexError:
        return False
    return domain in ws.allowed_domains
