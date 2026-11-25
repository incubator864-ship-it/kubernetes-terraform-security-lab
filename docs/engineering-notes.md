# Engineering notes

## Why local first

A disposable kind cluster allows repeated changes without cloud charges. It does not demonstrate AWS networking, EKS IAM, or managed control plane operations. Add an EKS phase only after the baseline works and costs are reviewed.

## Why Terraform stops at the cluster boundary

kind creates the cluster. Terraform then uses a fixed lab context to manage Kubernetes objects. This avoids bootstrapping the provider from a cluster that does not yet exist and reduces accidental targeting of work contexts.

## Why no network isolation claim

No NetworkPolicy is installed in this version. Network isolation requires both policy resources and a CNI that enforces them. Add and test that separately, including positive and negative connectivity tests.

## Detection work to add

Kubernetes audit events can show API operations such as pods/exec and denied secret reads. They do not prove which commands ran inside a container. Runtime process telemetry is a separate source. Establish ingestion and field mappings before claiming detection coverage in Splunk or Falcon.
