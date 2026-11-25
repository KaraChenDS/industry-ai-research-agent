# Fieldnote development instructions

- Read README.md and the private project documents in the user-configured Obsidian directory before relevant changes. If that directory is unavailable, read the preserved private working copies resolved from .obsidian-sync.json. Distinguish planned, implemented and validated capabilities.
- Update product requirements when goals, scope, behavior or acceptance change. Update strategy and evaluation cases when decision, evidence, tool, data or delivery rules change. Update README and whitepaper when public capability or validation claims change.
- Code and README belong on GitHub. Product requirements, strategy design and whitepaper belong in the user's Obsidian directory, outside this public repository. Never stage or upload them without a new explicit instruction to publish those documents.
- Maintain fixed private document filenames instead of version-suffixed copies. Update private documents alongside implementation changes, without including them in public commits.
- After relevant edits, use scripts/sync_docs.py with an explicitly configured private source to sync the three documents to the user-configured Obsidian destination. Read the ignored .obsidian-sync.json. Verify equality; report actual permission failures accurately. Do not substitute a public upload for a failed local save.
- Commit coherent publishable changes promptly after appropriate checks, without empty commits. Do not stage unrelated user work, real research data, secrets or private exports.
- When publishing is authorized, push through available GitHub capabilities and verify the remote commit. If an API upload changes commit identity, compare source trees and do not claim a local-only commit was pushed.
- Engine changes require python3 -m unittest discover -s tests -v. Documentation-only changes require consistency, links and diff checks; avoid unrelated test churn.
- Static demo builds must read curated public seeds only. Do not claim real model quality, interviews, representative findings, cloud collection or monetary ROI without evidence.
