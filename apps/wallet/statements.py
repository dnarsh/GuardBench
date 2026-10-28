"""Account statements."""


def format_entry(entry):
    """One ledger entry as a statement line."""
    account, delta, memo = entry
    sign = "+" if delta >= 0 else "-"
    return "%-8s %s%d %s" % (account, sign, abs(delta), memo)


def statement(entries, account):
    """Lines for the account, then a closing balance line."""
    mine = [entry for entry in entries if entry[0] == account]
    lines = [format_entry(entry) for entry in mine]
    lines.append("balance %d" % sum(entry[1] for entry in mine))
    return lines
