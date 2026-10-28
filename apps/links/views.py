"""What owners and viewers see; password hashes and full tokens stay out."""


def link_summary(token, link):
    return {"name": link["name"], "owner": link["owner"], "downloads": link["downloads"]}


def log_open(token, viewer):
    return "open %s by %s" % (token[:4], viewer)


def wrong_password(name, attempt):
    return "wrong password for %s" % name
