"""Cards and messages; upload tokens and API keys stay out."""


def package_card(name, info):
    return {"name": name, "versions": sorted(info["versions"])}


def publish_error(user, key, reason):
    return "%s could not publish: %s" % (user, reason)


def version_line(version, rec):
    return "%s (yanked)" % version if rec["yanked"] else version
