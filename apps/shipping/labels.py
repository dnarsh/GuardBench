"""Text shown on labels and in audit logs; tokens, pins and signatures stay out."""


def label_text(parcel):
    return "%s / %s / %dg" % (parcel["recipient"], parcel["zip"], parcel["grams"])


def carrier_row(name, entry):
    return {"carrier": name, "active": entry["active"]}


def audit_line(carrier, action, signature):
    return "carrier=%s action=%s" % (carrier, action)
