# Bitrig Agent Project Bridge Marketplace

This repository is a Codex marketplace source for the `bitrig-agent-project-bridge` plugin.

The plugin guides Codex through preparing a native Bitrig Agent project from a local iOS project, verifying local Bitrig evidence, and telling the user exactly what must be confirmed in Bitrig Remote on iPhone.

## What It Does

- Detects whether a local project looks iOS-capable.
- Rejects generic project identities unless a specific Agent name is supplied.
- Generates a Bitrig Agent prompt that asks for a native Agent project, not a Classic import.
- Keeps setup progress explicit: preflight, project, Bitrig, verify, remote.
- Verifies local Bitrig state before asking the user to check Bitrig Remote.

## What The User Must Verify

Codex can inspect local files and Bitrig state on the Mac. The user must still confirm the real iPhone-side result:

- Bitrig Remote is connected to the Mac.
- The generated project appears under **Agent**, not Classic.
- The generated Agent opens on iPhone.

The plugin must not claim Bitrig Remote success until the user confirms those points.

## Install From A Marketplace Source

From Codex CLI, add this repository as a marketplace source:

```bash
codex plugin marketplace add <repository-url>
```

Then open the Codex plugin directory, choose the marketplace named `bitrig-agent-project-bridge-marketplace`, and install **Bitrig Agent Project Bridge**.

After installation, start a new Codex thread and invoke:

```text
@bitrig-agent-project-bridge
```

or:

```text
Use $bitrig-agent-project-bridge to prepare a Bitrig Agent project from this local iOS project.
```

## Publish To A Public Repository

1. Run the release gate:

```bash
RELEASE_FORBIDDEN_TERMS="term-one,term-two" python3 scripts/release_check.py
```

2. Build a clean archive from tracked files:

```bash
python3 scripts/package_release.py --version 0.2.0
```

3. Upload the repository contents, or the generated archive contents, to a public Git repository.

4. Verify from another Codex installation or a clean profile:

```bash
codex plugin marketplace add <public-repository-url>
codex plugin add bitrig-agent-project-bridge@bitrig-agent-project-bridge-marketplace
codex plugin list
```

If another local plugin with the same name is already installed, remove or disable the older one before testing public installation. Duplicate plugin names can make invocation ambiguous even when the public package is valid.

You can also run the automated clean-profile verifier before publishing:

```bash
python3 scripts/verify_clean_codex_install.py
```

After publishing, verify the public repository URL directly:

```bash
python3 scripts/verify_clean_codex_install.py --source <public-repository-url>
```

## Local Development

Run the release checks:

```bash
python3 scripts/release_check.py
```

To add extra private terms to the scrub gate without storing them in the repository:

```bash
RELEASE_FORBIDDEN_TERMS="term-one,term-two" python3 scripts/release_check.py
```

The release gate validates marketplace metadata, plugin metadata, skill frontmatter, Python helper compilation, dry-run behavior, generic-name rejection, and hardcoded user-home path removal.

Verify that Codex can install the marketplace into a clean profile:

```bash
python3 scripts/verify_clean_codex_install.py
```

Verify an already-published source:

```bash
python3 scripts/verify_clean_codex_install.py --source <repository-url> --ref main
```

Build a clean source archive:

```bash
python3 scripts/package_release.py
```

Archives are written under `dist/` and intentionally exclude Git internals, runtime output, and ignored cache files.

## Runtime Commands

Dry run:

```bash
python3 plugins/bitrig-agent-project-bridge/skills/bitrig-agent-project-bridge/scripts/bitrig_agent_bridge.py run --project /path/to/ios-project --dry-run
```

Prepare setup files:

```bash
python3 plugins/bitrig-agent-project-bridge/skills/bitrig-agent-project-bridge/scripts/bitrig_agent_bridge.py prepare --project /path/to/ios-project
```

Verify local Bitrig evidence after Bitrig creates the Agent:

```bash
python3 plugins/bitrig-agent-project-bridge/skills/bitrig-agent-project-bridge/scripts/bitrig_agent_bridge.py verify --name ExampleAgent --source-path /path/to/ios-project
```

## Public-Safety Rules

- Do not include personal names, private paths, local machine names, or private project names in plugin source.
- Do not use Classic import as a fallback for Agent setup.
- Do not directly edit Bitrig index files as the primary creation path.
- Do not treat local verification as iPhone-side Bitrig Remote verification.
