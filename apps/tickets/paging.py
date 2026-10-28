"""Pages and service-level windows."""


def page(items, number, size):
    start = (number - 1) * size
    return items[start:start + size]


def overdue(tickets, today, sla_days):
    return [t for t in tickets if today - t["opened"] >= sla_days]


def page_count(total, size):
    return (total + size - 1) // size
