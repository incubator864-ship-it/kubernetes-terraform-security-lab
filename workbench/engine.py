"""Compare login detections on normalized, synthetic CloudTrail shaped events."""
import ipaddress
from datetime import datetime


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return result


def evaluate(event, rule, tuned=False):
    """Return alert, clear, or gap. Ground truth never enters this function."""
    if event.get("eventName") != "ConsoleLogin":
        return "clear", "outside rule scope"
    try:
        address = ipaddress.ip_address(event["sourceIPAddress"])
        moment = timestamp(event["eventTime"])
        identity = event["userIdentity"]
        if not identity.get("arn") or not identity.get("accountId"):
            raise ValueError("missing identity")
        response = event["responseElements"]["ConsoleLogin"]
        mfa = event["additionalEventData"]["MFAUsed"]
        if response not in ("Success", "Failure") or mfa not in ("Yes", "No"):
            raise ValueError("unexpected login fields")
    except (KeyError, ValueError, TypeError, AttributeError):
        return "gap", "missing or invalid required login fields"
    if any(address in ipaddress.ip_network(cidr) for cidr in rule["trusted_cidrs"]):
        return "clear", "trusted source network; credential abuse here is a known blind spot"
    if tuned:
        for exception in rule["exceptions"]:
            if (identity["arn"] == exception["principal_arn"]
                    and identity["accountId"] == exception["account_id"]
                    and str(address) == exception["source_ip"]
                    and response == exception["result"]
                    and mfa == exception["mfa_used"]
                    and timestamp(exception["valid_from"]) <= moment
                    < timestamp(exception["expires_at"])):
                return "clear", "matched scoped, time bounded lab exception"
    return "alert", "console login outside trusted source networks"


def validate_rule(rule):
    if not rule.get("trusted_cidrs"):
        raise ValueError("trusted_cidrs cannot be empty")
    for cidr in rule["trusted_cidrs"]:
        ipaddress.ip_network(cidr)
    for item in rule["exceptions"]:
        if not item.get("owner") or not item.get("justification"):
            raise ValueError("exceptions require owner and justification")
        ipaddress.ip_address(item["source_ip"])
        if timestamp(item["valid_from"]) >= timestamp(item["expires_at"]):
            raise ValueError("exception expiry must follow its start")


def compare(source, ingested, rule, labels):
    validate_rule(rule)
    source_ids = [item["eventID"] for item in source]
    ingested_ids = [item["eventID"] for item in ingested]
    if len(set(source_ids)) != len(source_ids) or len(set(ingested_ids)) != len(ingested_ids):
        raise ValueError("duplicate eventID; deduplicate explicitly before comparison")
    if set(ingested_ids) - set(source_ids):
        raise ValueError("ingested event absent from source reference")
    versions = {}
    for name, tuned in (("baseline", False), ("tuned", True)):
        outcomes = {item["eventID"]: dict(zip(("status", "reason"), evaluate(item, rule, tuned)))
                    for item in ingested}
        counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "unknown": 0, "gaps": 0}
        for event_id, outcome in outcomes.items():
            if outcome["status"] == "gap":
                counts["gaps"] += 1
                continue
            label = labels.get(event_id)
            if label not in ("malicious", "benign"):
                counts["unknown"] += 1
                continue
            key = {
                ("malicious", "alert"): "tp", ("malicious", "clear"): "fn",
                ("benign", "alert"): "fp", ("benign", "clear"): "tn",
            }[(label, outcome["status"])]
            counts[key] += 1
        versions[name] = {"counts": counts, "outcomes": outcomes}
    baseline = versions["baseline"]["outcomes"]
    tuned = versions["tuned"]["outcomes"]
    removed = sorted(key for key in baseline if baseline[key]["status"] == "alert"
                     and tuned[key]["status"] != "alert")
    missing = sorted(set(source_ids) - set(ingested_ids))
    return {
        "data_kind": "synthetic lab fixtures, not production performance",
        "versions": versions,
        "removed_alert_ids": removed,
        "removed_malicious_ids": [key for key in removed if labels.get(key) == "malicious"],
        "missing_source_ids": missing,
        "missing_malicious_ids": [key for key in missing if labels.get(key) == "malicious"],
        "source_count": len(source), "ingested_count": len(ingested),
        "limitation": "Metrics cover labeled, evaluable ingested fixtures only. Gaps and missing events are separate."
    }
