"""Subscriptions: which user follows which feed, and which items were already delivered."""
import threading

HOOKS = {}


def checkpoint(name):
    """Test hook: lets a test interleave threads at a named point."""
    fn = HOOKS.get(name)
    if fn:
        fn()


class Subs:
    def __init__(self):
        self.feeds = {}
        self.subscriptions = {}
        self.unsub_tokens = {}
        self.seen = set()
        self.lock = threading.Lock()

    def add_feed(self, name, public=True, members=()):
        self.feeds[name] = {"public": public, "members": set(members)}

    def subscribe(self, user, feed, cap=2):
        with self.lock:
            mine = self.subscriptions.setdefault(user, [])
            if len(mine) >= cap:
                return False
            checkpoint("sub")
            mine.append(feed)
            return True

    def mark_seen(self, item_id):
        with self.lock:
            if item_id in self.seen:
                return False
            checkpoint("seen")
            self.seen.add(item_id)
            return True

    def unsubscribe(self, user, feed):
        mine = self.subscriptions.get(user, [])
        if feed in mine:
            mine.remove(feed)
            return True
        return False

    def feeds_of(self, user):
        return sorted(self.subscriptions.get(user, []))
