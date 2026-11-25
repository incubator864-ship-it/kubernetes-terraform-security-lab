# Engineering notes

## Why local first

A disposable kind cluster allows repeated changes without cloud charges. It does not demonstrate AWS networking, EKS IAM, or managed control plane operations. Add an EKS phase only after the baseline works and costs are reviewed.

## Why Terraform stops at the cluster boundary

kind creates the cluster. Terraform then uses a fixed lab context to manage Kubernetes objects. This avoids bootstrapping the provider from a cluster that does not yet exist and reduces accidental targeting of work contexts.

## Why no network isolation claim

No NetworkPolicy is installed in this version. Network isolation requires both policy resources and a CNI that enforces them. Add and test that separately, including positive and negative connectivity tests.

## Detection work to add

Kubernetes audit events can show API operations such as pods/exec and denied secret reads. They do not prove which commands ran inside a container. Runtime process telemetry is a separate source. Establish ingestion and field mappings before claiming detection coverage in Splunk or Falcon.

## Workbench deployment decision

The detection runner is a batch task, so a suspended CronJob is a better fit than an always running web service. Forbid prevents overlapping scheduled executions, backoff_limit is zero so an unhealthy replay is visible, and a deadline bounds execution. The container requires no Kubernetes API token and no AWS credentials. Manual Job creation exercises the same template.

A production scheduler still needs durable output, deduplication, late event handling, source freshness checks, and alert routing. The lab deliberately makes none of those claims.

## Live failure: container security context overrides pod settings

The first cluster rollout was blocked by Pod Security admission. ReplicaSet events reported that the container set runAsNonRoot=false, despite a pod-level true value in the Terraform source. Explicitly setting run_as_non_root=true in each container security context fixes that conflict without weakening the restricted namespace. Terraform validation alone did not reveal this runtime behavior. Failure diagnostics now capture ReplicaSet and Pod events before cleanup.
