#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required."
  exit 1
fi

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

if [[ -z "${REPO}" ]]; then
  echo "Unable to detect repository. Pass owner/repo as the first argument."
  exit 1
fi

configure_environment() {
  local environment_name="$1"
  local wait_seconds="$2"

  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/environments/${environment_name}" \
    --input - <<JSON
{
  "wait_timer": ${wait_seconds},
  "reviewers": [],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
JSON
}

configure_branch_protection() {
  local branch_name="$1"

  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/branches/${branch_name}/protection" \
    --input - <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "lint",
      "test"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": false
}
JSON
}

echo "Configuring environments for ${REPO}..."
configure_environment development 0
configure_environment staging 60
configure_environment production 180

echo "Configuring branch protections for ${REPO}..."
configure_branch_protection dev
configure_branch_protection test
configure_branch_protection main

echo "Done."
