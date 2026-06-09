# OpenAI Curated Marketplace Review Request

Title: Request to review Bitrig Agent Project Bridge for the OpenAI-curated Codex plugin marketplace

Repository: https://github.com/OBXfund/Codex-to-Bitrig-Remote-Simulator

Plugin: `bitrig-agent-project-bridge`

Marketplace: `bitrig-agent-project-bridge-marketplace`

## Summary

Bitrig Agent Project Bridge is a Codex plugin that helps users turn a local Codex-created iOS project into a native Bitrig Agent project that can appear in Bitrig Remote on iPhone. It guides Codex through project preflight, Agent-name derivation, prompt generation, Bitrig setup, local verification, and explicit iPhone-side confirmation.

## User Value

- Helps Codex users bridge local Swift, SwiftUI, Xcode, or iOS-capable projects into Bitrig Remote.
- Avoids accidental Classic imports by requiring the native Bitrig Agent creation path.
- Rejects generic project names such as `New Project` unless the user supplies a specific Agent name.
- Keeps local verification separate from user-confirmed Bitrig Remote visibility.

## Public Install

```bash
codex plugin marketplace add https://github.com/OBXfund/Codex-to-Bitrig-Remote-Simulator.git
codex plugin add bitrig-agent-project-bridge@bitrig-agent-project-bridge-marketplace
```

## Verification Performed

- `python3 scripts/release_check.py`
- `python3 scripts/verify_clean_codex_install.py`
- Public HTTPS marketplace install from the GitHub repository
- Public raw marketplace access at `.agents/plugins/marketplace.json`

## Security And Privacy Notes

- The plugin does not include credentials.
- The plugin does not include private user paths in packaged source.
- The workflow tells Codex to inspect local project files and Bitrig state only with user approval.
- The plugin does not claim iPhone-side Bitrig Remote success until the user confirms the project appears and opens on iPhone.
- The plugin does not use Classic import as a fallback and does not directly mutate Bitrig index files as the primary creation path.

## Request

Please review this public Codex plugin for possible inclusion in the OpenAI-curated Codex plugin marketplace, or advise on the correct submission path if a separate curation intake is required.
