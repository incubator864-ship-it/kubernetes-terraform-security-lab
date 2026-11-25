# Live deployment evidence

[Successful GitHub Actions run](https://github.com/incubator864-ship-it/kubernetes-terraform-security-lab/actions/runs/45659969560)

Code commit: `423c87a`. Artifact: `replay-evidence`, ID `15043509066`, containing cluster-replay.json, comparison.json, and evaluable.json. Artifact retention is 14 days.

## What was executed

The runner built the Python image, created a disposable kind cluster, loaded the image, applied six Terraform resources, and ran scripts/verify_cluster.sh. The script verified:

- Observer can list pods but cannot get secrets.
- Baseline workload UID is 65532 and no API service account token is mounted.
- A root filesystem write is rejected.
- Server-side admission rejects an unrestricted pod.
- A Job created from the suspended CronJob completes and emits the expected JSON replay.

Cleanup deleted the cluster. The Actions result, not this document alone, is the execution evidence.

## Independently checked cluster output

| Version | True positives | False positives | False negatives | True negatives | Unknown | Gaps |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline | 4 | 4 | 1 | 1 | 1 | 0 |
| Tuned | 4 | 0 | 1 | 5 | 1 | 0 |

Removed alerts: e01, e02, e03, e04. Removed malicious alerts: none. Missing source IDs in the complete replay: none. These are synthetic fixture counts, not claims about production performance.

## Failure that validation missed

[Diagnostic failed run](https://github.com/incubator864-ship-it/kubernetes-terraform-security-lab/actions/runs/45657332589)

Terraform configuration validation passed, but Pod Security rejected the generated workload. ReplicaSet events reported:

```text
violates PodSecurity "restricted:latest": runAsNonRoot != true
(container "app" must not set securityContext.runAsNonRoot=false)
```

The pod-level setting was true, but the container-level value overrode it. Both Terraform container security contexts now explicitly set run_as_non_root=true. The successful run verifies that fix with restricted admission still enabled. No namespace policy was weakened.

## Limits

No AWS resources were created. No real Elastic, Splunk, or Falcon tenant was connected. Network isolation and live ingestion were not tested. A trusted source network remains a known detection blind spot. A green build does not establish production readiness or complete attack coverage.
