"""Rows and messages for operators; fence tokens stay out."""


def lease_row(name, lease):
    return {"name": name, "holder": lease["holder"], "expires": lease["expires"]}


def denied(name, holder, token):
    return "%s may not renew lease %s" % (holder, name)


def summary_line(table):
    return "%d lease(s): %s" % (len(table.leases), ", ".join(table.names()))
