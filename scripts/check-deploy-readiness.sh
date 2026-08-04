#!/usr/bin/env sh
set -eu

for required_file in Dockerfile docker-compose.prod.yml DEPLOYMENT.md; do
  test -f "$required_file" || { echo "Missing deployment prerequisite: $required_file" >&2; exit 1; }
done

grep -q '/_stcore/health' Dockerfile
grep -q '/_stcore/health' docker-compose.prod.yml
grep -q 'Persistence: stateless' DEPLOYMENT.md
grep -q 'Backup: not applicable' DEPLOYMENT.md
grep -q 'Rollback by activating the previous immutable image' DEPLOYMENT.md
if grep -qE '^[[:space:]]+ports:' docker-compose.prod.yml; then
  echo "Private service must not publish host ports" >&2
  exit 1
fi

echo "Deployment prerequisites verified."
