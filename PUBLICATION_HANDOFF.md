# Public Marketplace Publication Handoff

This repository contains the clean Codex marketplace-root source for `bitrig-agent-project-bridge`.

## Current State

- Local clean marketplace commit: `0bcc1aed78ee1918e3f186c57972c9542b985398`
- Public repository: `https://github.com/OBXfund/Codex-to-Bitrig-Bridge.git`
- Public `main` currently points to: `bd88ef2f5d95817b2e3a1dbbaffd79eadbae2ec1`
- Public `main` is not currently a valid Codex marketplace root because it does not expose `.agents/plugins/marketplace.json` at the repository root.

## Why Replacement Is Needed

The current public branch contains prior bridge/demo files and an uploaded zip. Codex marketplace installation requires the marketplace manifest and plugin package to be present directly in the repository tree.

The clean local source already has that shape:

```text
.agents/plugins/marketplace.json
plugins/bitrig-agent-project-bridge/.codex-plugin/plugin.json
plugins/bitrig-agent-project-bridge/skills/bitrig-agent-project-bridge/SKILL.md
```

The current public branch also contains local machine paths from earlier bridge artifacts. The clean local source passes the private-term and user-home-path scrub gates.

## Publish Command

Run this from the clean local checkout after GitHub authentication is available:

```bash
python3 scripts/publish_public.py https://github.com/OBXfund/Codex-to-Bitrig-Bridge.git --force-with-lease
```

This command:

- Requires a clean worktree.
- Runs the release checks.
- Verifies clean local Codex marketplace installation.
- Pushes `main` with lease protection.
- Verifies clean Codex marketplace installation from the public GitHub source.

## Manual Equivalent

If you prefer manual Git commands:

```bash
git push --force-with-lease origin main
python3 scripts/verify_clean_codex_install.py --source https://github.com/OBXfund/Codex-to-Bitrig-Bridge.git --ref main
```

Use `--force-with-lease` because the public branch is currently an unrelated uploaded-file history. Lease protection prevents replacing newer remote work you have not fetched.

## Expected Success

After publication, this command should pass:

```bash
python3 scripts/verify_clean_codex_install.py \
  --source https://github.com/OBXfund/Codex-to-Bitrig-Bridge.git \
  --ref main
```

Then another Codex user can install with:

```bash
codex plugin marketplace add https://github.com/OBXfund/Codex-to-Bitrig-Bridge.git --ref main
codex plugin add bitrig-agent-project-bridge@bitrig-agent-project-bridge-marketplace
```
