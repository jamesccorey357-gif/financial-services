## What changed

<!-- One or two sentences. Which plugin(s) / agent(s) does this touch? -->

## Checklist

- [ ] `python3 scripts/check.py` passes
- [ ] Skills edited in `plugins/vertical-plugins/`, then synced with `python3 scripts/sync-agent-skills.py` (not edited directly in `agent-plugins/`)
- [ ] Changed plugins have a version bump (the pre-commit hook does this for you)
- [ ] Any `.ps1` files are pure ASCII (no em dashes or curly quotes)
- [ ] Cookbook changes: `bash scripts/test-cookbooks.sh` passes

Tip: comment `@claude` on this PR to ask for a review or a fix.
