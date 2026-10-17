# Azure Repos and GitHub synchronization

Azure Repos (`origin`) owns CI, Test CD and the required build-validation policy.
GitHub (`github`) is the public portfolio mirror. Their histories are independent;
the public cleanup changed commit identities. Compare tree IDs and file contents,
not commit IDs, when verifying a mirror.

## Verified controls on 17 October 2026

| Repository / environment | Verified control |
| --- | --- |
| Azure `main` | Enabled, blocking build validation using `EV-Analytics-CI` (definition 1), exact `main` scope, automatically queued. |
| Azure Test | `EV-Analytics-Test` has an Exclusive lock; CD uses sequential lock behavior. |
| GitHub `main` | PR required, administrators included, conversation resolution required, force-push and branch deletion disabled. |
| GitHub reviews | Zero external approvals for this personal portfolio; code-owner and last-pusher approval are disabled. |
| GitHub status checks | No required status context is configured: the Azure Repos pipeline does not publish a GitHub check. Validate the matching Azure source before merging the mirror PR. |

GitHub protection was applied and read back through the API. The Azure policy
and environment lock were inspected without modification. Settings outside this
table, including every user's effective bypass permission, have not been audited.

## Change and mirror procedure

1. Create a feature branch in Azure Repos. Complete CI and use its selected
   `ev-test-release` artifact for Test CD; retain the commit/build identities.
2. Review the change and merge through Azure's required build policy.
3. Fetch both remotes. If their trees differ, create a mirror branch **from
   `github/main`**, then apply only the reviewed change. Never merge the entire
   Azure history into the public history or use `push --mirror` / force-push.
4. Compare the mirror branch tree to the accepted Azure source. Resolve every
   differing file before creating a GitHub PR. Preserve the public author's
   configured commit identity and exclude local evidence, data and credentials.
5. Merge the GitHub PR, fetch again and run the content check below. Save the
   two commit IDs, shared tree ID and PR/build links in the acceptance record.

```powershell
git fetch --no-tags origin main
git fetch --no-tags github main
python scripts/check_repository_sync.py --output output/repository-sync.json
```

The command exits nonzero when trees differ and lists the differing paths. It
checks fetched refs; it does not fetch, push or change either repository. Before
this acceptance change, Azure `fa9e0fa` and GitHub `c4cd4a2` shared tree
`62e219fcd5873adbeacf5de55342dcfe7e497112` despite different commit IDs.

GitHub's [protection API](https://docs.github.com/en/rest/branches/branch-protection#update-branch-protection)
documents the PR/reviewer settings. Azure's [branch-policy guide](https://learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies)
documents the repository-side build-validation policy.
