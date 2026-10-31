"""Prospective eligibility policy for confirmatory hypothesis reporting.

Registry records, not caller-supplied flags, identify eligible cohorts. Adding a
future cohort requires a committed prospective protocol amendment. Reviewer role
is a declaration, not an authenticated identity.
"""

TARGET = 150

PROTOCOLS = {
    "prereg-v3": {
        "manifest": "ae29a20ee5b1f9e2a86d714805f5e20776148f268ef9e45375ef70b7c5927990",
        "apps_hash": "8b3fd772266b3ec05f073db8a3632d10ae99507c2879b304d7fb7a3b4f97cc1d",
        "n": 100,
        "mode": "pilot",
        "minimum": TARGET,
    },
}


def assess_eligibility(metadata, n):
    """Return eligibility and stable reasons for an analysis metadata block.

    ``metadata`` is the ``analysis`` member of a run summary. Only a registered
    confirmatory cohort can be eligible; the current prereg-v3 cohort is pilot
    regardless of the purpose or eligibility flags supplied by the caller.
    """
    if not isinstance(metadata, dict):
        return {"eligible": False, "reasons": ["analysis metadata is missing or malformed"]}

    reasons = []
    if type(metadata.get("schema_version")) is not int or metadata["schema_version"] != 1:
        reasons.append("analysis schema_version must be 1")
    if metadata.get("purpose") != "confirmatory":
        reasons.append("analysis purpose must be confirmatory")
    if metadata.get("split") != "heldout":
        reasons.append("analysis split must be heldout")

    valid_n = type(n) is int and n >= 0
    if not valid_n:
        reasons.append("defect count must be a nonnegative integer")

    protocol = metadata.get("protocol")
    record = PROTOCOLS.get(protocol) if isinstance(protocol, str) else None
    if record is None:
        reasons.append("analysis protocol is not registered")
    else:
        if record["mode"] != "confirmatory":
            reasons.append("registered cohort is pilot-only")
        dataset = metadata.get("dataset")
        dataset = dataset if isinstance(dataset, dict) else {}
        if dataset.get("manifest") != record["manifest"]:
            reasons.append("dataset manifest does not match the registered cohort")
        if dataset.get("apps_hash") != record["apps_hash"]:
            reasons.append("dataset apps_hash does not match the registered cohort")
        if valid_n:
            if n != record["n"]:
                reasons.append("defect count does not match the registered cohort")
            if n < max(TARGET, record["minimum"]):
                reasons.append("defect count is below the registered minimum")

    reviewer = metadata.get("reviewer")
    reviewer = reviewer if isinstance(reviewer, dict) else {}
    label = reviewer.get("label")
    if not isinstance(label, str) or not label.strip():
        reasons.append("reviewer label is missing or invalid")
    if reviewer.get("role") not in ("model", "human"):
        reasons.append("reviewer role must be model or human")
    if reviewer.get("transport") not in ("command", "callable"):
        reasons.append("reviewer transport must be command or callable")

    return {"eligible": not reasons, "reasons": reasons}
