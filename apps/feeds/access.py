"""Read access and unsubscribe-token checks."""
import hmac


def may_read(subs, user, feed):
    info = subs.feeds.get(feed)
    if info is None:
        return False
    return info["public"] or user in info["members"]


def valid_unsub_token(subs, user, token):
    try:
        expected = subs.unsub_tokens[user]
    except KeyError:
        return False
    return hmac.compare_digest(expected, token)
