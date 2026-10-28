"""Stock reports and alerting."""


def low_stock(stock, threshold):
    """SKUs whose level is at or below threshold, sorted."""
    return [sku for sku in stock.skus() if stock.available(sku) <= threshold]


def alert_low(stock, notifier, threshold):
    """Alert for every low SKU; returns how many alerts were sent."""
    low = low_stock(stock, threshold)
    for sku in low:
        notifier.alert(sku, stock.available(sku))
    return len(low)


def levels_table(stock):
    """Aligned 'sku  qty' lines."""
    return ["%-10s %5d" % (sku, stock.available(sku)) for sku in stock.skus()]
