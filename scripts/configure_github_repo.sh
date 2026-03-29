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

  # Some GitHub plans (especially private repos on Free) do not support
  # deployment protection rules (wait timers/reviewers). Try full settings
  # first, then gracefully fall back to creating a basic environment.
  if gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/environments/${environment_name}" \
    --input - >/dev/null <<JSON
{
  "wait_timer": ${wait_seconds},
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
JSON
  then
    echo "Configured environment '${environment_name}' with wait timer ${wait_seconds}s."
    return 0
  fi

  echo "Warning: advanced environment protection is not available for '${environment_name}'. Falling back to basic environment."

  if gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${REPO}/environments/${environment_name}" >/dev/null
  then
    echo "Configured basic environment '${environment_name}'."
    return 0
  fi

  echo "Warning: unable to configure environment '${environment_name}'. Continuing."
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
