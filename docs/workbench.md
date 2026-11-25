# Detection tuning workbench

## The problem

Reducing alert volume can hide attacks. This exercise compares individual event matches, not only counts, and separates missing telemetry from tuning results.

All input is invented. Addresses use documentation networks, account IDs are fictional, and labels are lab ground truth. No interview content or employer data is included.

## Run without a cluster

Python 3.9 or newer is sufficient. There are no third party Python dependencies.

```bash
python3 -m unittest discover -s tests -v
python3 -m workbench --output reports/comparison.json
```

The default replay intentionally exits **4**: event e07 exists at the source but is missing from ingestion, and e09/e12 lack usable source addresses. This is a successful demonstration of an unhealthy pipeline, not a successful healthy run.

For a complete, evaluable replay:

```bash
python3 -m workbench --source examples/evaluable.json --ingested examples/evaluable.json --output reports/evaluable.json
```

Exit codes: 0 means no new tuning regression or observed telemetry gap in supplied inputs; 2 means invalid input; 3 means tuning removed a labeled malicious alert; 4 means missing or malformed telemetry. Exit 0 does not mean complete attack coverage.

## Rule and ground truth

The baseline alerts on console logins outside the lab trusted CIDR. The tuned rule adds one exact exception requiring the principal ARN, account ID, IP, successful result, MFA, and event time within a defined interval. Expiry is exclusive. Historical replay evaluates the exception at event time, not the machine's current clock.

The exception represents manually verified expected activity. It is not a recommendation to trust automation merely because an account name looks familiar. Requiring MFA in the exception preserves the no-MFA case, but MFA itself is not proof of safety.

Labels live in examples/labels.json and enter scoring only. They never enter detection evaluation. Unknown dispositions are not classified as benign. In real investigations, a matched rule can correctly detect expected activity; do not reuse these binary fixture labels as a production disposition model.

## Cases to explain

| IDs | Scenario | Expected tuned result |
| --- | --- | --- |
| e01 to e04 | Exact approved exception | Clear |
| e05 | Same principal, different source | Alert |
| e06 | Same principal, no MFA | Alert |
| e07 | Different principal from approved source | Alert if ingested; missing in outage fixture |
| e08 | Malicious use from trusted network | Missed by both rules, known blind spot |
| e09, e12 | Missing or malformed source IP | Telemetry gap, excluded from confusion matrix |
| e10 | Expected trusted network login | Clear |
| e11 | Event exactly at exception expiry | Alert |
| e13 | Failed login, unresolved disposition | Alert, unknown in scoring |

Inspect reports/comparison.json and reports/evaluable.json for actual outcomes. The evaluable replay removes four false positives, preserves four malicious alerts, and still misses e08. These are fixture counts, not production improvement claims.

## Telemetry failure exercise

Compare source.json with ingested.json. Trace the missing event ID, separate the source evidence from the destination evidence, and write an escalation containing the affected interval, missing event IDs, dependent detections, and source/destination counts. Do not infer a queue or Lambda root cause from this fixture alone.

This version compares a complete source reference with an ingestion snapshot. It does not implement live freshness monitoring, queue metrics, ingestion lag, retries, or a production transport.

## Kubernetes execution

Build the image, load it into kind, then apply Terraform from terraform/. The CronJob starts suspended to avoid repeated jobs until you deliberately enable scheduling. It uses the complete/evaluable fixture. The default CLI remains the outage demonstration.

```bash
docker build -t detection-workbench:lab .
kind create cluster --name security-lab --wait 180s
kind load docker-image detection-workbench:lab --name security-lab
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=lab.tfplan
terraform -chdir=terraform apply lab.tfplan
bash scripts/verify_cluster.sh
```

The check script verifies RBAC denial, nonroot UID, absent service account token, filesystem restrictions, Pod Security admission, and a completed replay Job. It writes the Job's actual JSON output to reports/cluster-replay.json. The image runs without cloud credentials or Kubernetes API access.

## Your practice tasks

1. Before running anything, predict which IDs each rule alerts on and explain e08.
2. Change only the exception expiry. Run tests and inspect which matches change.
3. Add a malicious case that almost matches the exception. Write its expected outcome before editing the rule.
4. Break ingestion by removing a second event. Produce an escalation without claiming a root cause you cannot prove.
5. Make a deliberately unsafe exception, observe removed_malicious_ids, then roll back the rule with Git.
6. Delete a lab pod and inspect controller recovery. Diagnose an intentionally wrong CronJob image tag, then restore it with Terraform.

Do these exercises yourself and record what happened. The code being generated is not a substitute for operating it.

## Next phases

An AWS S3/Athena execution path, Elastic or Splunk field mappings, live telemetry, Falcon coverage, and network isolation are not implemented here. Add one source integration at a time and validate against this shared fixture set. Raw CloudTrail delivery files need explicit parsing and normalization; this workbench accepts normalized JSON arrays, not arbitrary vendor payloads.
