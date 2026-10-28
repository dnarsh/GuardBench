"""Invoice rows and messages; card tokens and card numbers stay out."""


def invoice_row(name, acct):
    return {"account": name, "plan": acct["plan"], "used": acct["used"]}


def charge_failed(name, card):
    return "charge failed for %s (card ending %s)" % (name, card[-4:])


def total_used(rows):
    return sum(row["used"] for row in rows)


def invoice_title(number):
    return "INV-%d" % number
