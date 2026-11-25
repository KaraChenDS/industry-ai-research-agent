# Fieldnote development instructions

- Read README.md, docs/product-requirements.md, docs/agent-strategy.md and docs/whitepaper.md before relevant changes. Distinguish planned, implemented and validated capabilities.
- Update product requirements when goals, scope, behavior or acceptance change. Update strategy and evaluation cases when decision, evidence, tool, data or delivery rules change. Update README and whitepaper when public capability or validation claims change.
- Maintain fixed document filenames instead of version-suffixed copies. Commit documentation with the meaningful implementation changes it describes.
- After relevant edits, use scripts/sync_docs.py to sync the three documents to the user-configured Obsidian destination. Read .obsidian-sync.json if present. Verify equality; report actual permission failures accurately.
- Commit coherent publishable changes promptly after appropriate checks, without empty commits. Do not stage unrelated user work, real research data, secrets or private exports.
- When publishing is authorized, push through available GitHub capabilities and verify the remote commit. If an API upload changes commit identity, compare source trees and do not claim a local-only commit was pushed.
- Engine changes require python3 -m unittest discover -s tests -v. Documentation-only changes require consistency, links and diff checks; avoid unrelated test churn.
- Static demo builds must read curated public seeds only. Do not claim real model quality, interviews, representative findings, cloud collection or monetary ROI without evidence.
