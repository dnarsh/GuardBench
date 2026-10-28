"""Low-stock alerts sent to a webhook."""


class Notifier:
    def __init__(self, url, api_key, sender=None):
        self.url = url
        self.api_key = api_key
        self.sender = sender  # callable(url, headers, body); None only logs
        self.log = []

    def alert(self, sku, level):
        """Send one alert and return its text."""
        body = "low stock: %s has %d left" % (sku, level)
        headers = {"Authorization": "Bearer " + self.api_key}
        self.log.append("alert %s -> %s" % (sku, self.url))
        if self.sender is not None:
            self.sender(self.url, headers, body)
        return body
