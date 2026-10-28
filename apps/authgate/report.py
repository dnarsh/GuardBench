"""Summaries of the audit trail."""
from collections import Counter


def parse_entry(line):
    """'event k=v k2=v2' -> (event, {k: v})."""
    event, *parts = line.split(" ")
    fields = {}
    for part in parts:
        key, _, value = part.partition("=")
        fields[key] = value
    return event, fields


def count_by_event(entries):
    counts = Counter()
    for line in entries:
        event, _ = parse_entry(line)
        counts[event] += 1
    return dict(counts)


def failed_logins(entries):
    """Users with at least one failed login, sorted."""
    users = set()
    for line in entries:
        event, fields = parse_entry(line)
        if event == "login_failed":
            users.add(fields.get("user", "?"))
    return sorted(users)


def denied_actions(entries):
    """List of (user, action) pairs that were denied."""
    result = []
    for line in entries:
        event, fields = parse_entry(line)
        if event == "deny" and "action" in fields:
            result.append((fields.get("user", "?"), fields["action"]))
    return result


def format_summary(entries):
    counts = count_by_event(entries)
    lines = ["%-14s %d" % (event, counts[event]) for event in sorted(counts)]
    lines.append("failed logins: " + (", ".join(failed_logins(entries)) or "none"))
    return "\n".join(lines)
