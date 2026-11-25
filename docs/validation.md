# Validation record

Authoring checks performed November 24, 2026:

- Terraform 1.14.0 downloaded from HashiCorp; SHA256 matched official checksums.
- terraform fmt -check: passed.
- terraform init -backend=false: passed; HashiCorp Kubernetes provider 2.37.1 installed and signed by HashiCorp.
- terraform validate: passed.
- Provider lockfile generated and included.
- Live deployment, Terraform plan/apply, RBAC, workload, and admission checks: not run. Docker, kind, and kubectl are unavailable.
- Falcon and Splunk: not integrated or tested.

## Record after deployment

Record cluster version, commands, actual output, and failures. Expected output in the README is not test evidence.
