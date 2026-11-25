#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
k=(kubectl --context kind-security-lab --namespace security-lab)
mkdir -p reports
"${k[@]}" rollout status deployment/lab-app --timeout=180s
[[ "$("${k[@]}" auth can-i list pods --as=lab-observer)" == yes ]]
# can-i returns 1 for an expected denial; check the text as well.
answer=$("${k[@]}" auth can-i get secrets --as=lab-observer || true)
[[ "$answer" == no ]]
[[ "$("${k[@]}" exec deployment/lab-app -- id -u)" == 65532 ]]
"${k[@]}" exec deployment/lab-app -- sh -c 'test ! -e /var/run/secrets/kubernetes.io/serviceaccount/token'
# Separate an expected security rejection from unrelated execution failures.
output=$("${k[@]}" exec deployment/lab-app -- touch /should-fail 2>&1) && {
  echo 'FAIL: root filesystem was writable'; exit 1;
}
grep -Eiq 'read-only file system|permission denied' <<< "$output"
# Server-side dry run exercises admission without creating an insecure pod.
output=$("${k[@]}" run should-be-denied --image=busybox:1.37.0 --restart=Never --dry-run=server -o json 2>&1) && {
  echo 'FAIL: restricted admission allowed an unrestricted pod'; exit 1;
}
grep -q 'violates PodSecurity' <<< "$output"
job="replay-$(date +%s)"
"${k[@]}" create job "$job" --from=cronjob/detection-workbench
if ! "${k[@]}" wait --for=condition=complete "job/$job" --timeout=180s; then
  "${k[@]}" describe "job/$job"
  "${k[@]}" get pods
  "${k[@]}" logs "job/$job" || true
  exit 1
fi
"${k[@]}" logs "job/$job" > reports/cluster-replay.json
python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('reports/cluster-replay.json').read_text())
assert r['removed_alert_ids']==['e01','e02','e03','e04']
assert r['removed_malicious_ids']==[]
assert r['missing_source_ids']==[]
assert r['versions']['baseline']['counts']['fp']==4
assert r['versions']['tuned']['counts']['fp']==0
assert r['versions']['tuned']['counts']['fn']==1
assert r['versions']['tuned']['counts']['gaps']==0
print('PASS: cluster replay preserved expected detections and reported the known false negative.')
PY
printf '%s\n' 'PASS: RBAC, UID, token mount, filesystem, admission, and replay checks.'
