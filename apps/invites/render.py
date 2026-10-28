"""Rows and messages shown to people; codes and seeds stay private."""


def describe_invite(code, invite):
    return {"email": invite["email"], "role": invite["role"], "expires": invite["expires"]}


def member_row(email, member):
    return {"email": email, "role": member["role"]}


def accept_error(code, reason):
    return "cannot accept invite: %s" % reason
