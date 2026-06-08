---
name: bitrig-agent-project-bridge
description: Create a native Bitrig Agent project from any local Codex-created iOS project so Bitrig Remote can open and run it on iPhone. Use when the user asks to add a Codex iOS project to Bitrig, make a project visible under Bitrig Remote Agent, create a Bitrig Agent wrapper, or bridge a local Swift/SwiftUI/Xcode project into Bitrig without relying on Classic imports or plist-only project-index edits.
---

# Bitrig Agent Project Bridge

Use this skill to turn a local iOS project into a Bitrig-native Agent project visible under **Agent** in Bitrig and Bitrig Remote.

This public plugin must work on other Codex installations. Never assume a specific home directory, checkout path, user name, project name, or locally installed helper outside this plugin. Resolve bundled scripts relative to this `SKILL.md` file, use `Path.home()` for Bitrig's standard user-library locations, and explain every setup step before asking the user to act.

## Core Rule

Create the project through Bitrig's native Agent creation UI. Do not rely on manual `Projects.json` or `app.bitrig.AppIntents.ProjectIndex` insertion as the primary path; Bitrig prunes records that are not backed by native Agent state.

## Workflow

1. Start with a dry run unless the user has already approved setup.
   - Run `python3 scripts/bitrig_agent_bridge.py run --project <path> --dry-run`.
   - Confirm the project path exists and detects iOS-capable markers: `.xcodeproj`, `.xcworkspace`, `Package.swift`, `project.yml`, or Swift files.
   - Reject generic identities such as `New Project`, `App`, `Agent`, or `Untitled` unless the user supplies a clear `--agent-name`.
2. Prepare the Agent prompt and explain the next step.
   - Run `python3 scripts/bitrig_agent_bridge.py prepare --project <path>`.
   - Use the generated `agentName`, prompt file, and setup checklist.
   - The visible Agent name should default to `<SourceName>Agent`.
3. Open Bitrig's native Agent project creator.
   - Activate Bitrig with `open -a Bitrig` or `osascript`.
   - In Bitrig, use the Agent project list `+` button or `File > New Project`.
   - Make sure the prompt composer shows `Agent`, not Classic.
4. Paste and submit the generated prompt.
   - Put the prompt on the clipboard with `pbcopy < /path/to/generated-prompt.txt`.
   - Paste into the Bitrig New Project text field and submit.
   - Wait until Bitrig reports a successful build or shows a concrete error.
5. Verify the native Agent result.
   - Run `python3 scripts/bitrig_agent_bridge.py verify --name "AgentName" --source-path <path>`.
   - Confirm:
     - `ProjectIndex` has the newest row as `source=agent`.
     - `~/Library/Bitrig/Projects.json` has the project with `iPhone=true`.
     - `~/Library/Bitrig/Projects/<id>/Project.json` exists and has an iOS application target.
     - `~/Library/Bitrig/Projects/<id>/BitrigAgent.json` exists and references the source checkout.
     - Bitrig's Mac Agent list visually shows the project.
6. Ask the user to refresh Bitrig Remote and check **Agent** for the project.
   - The user must confirm the generated Agent appears in Bitrig Remote on iPhone and opens.
   - Do not claim Remote is verified until the user confirms it appears and opens on iPhone.

## User Communication Requirements

Keep the user informed in this order:

1. `Preflight`: say what local prerequisites are being checked.
2. `Project`: say which source path and Agent name were resolved.
3. `Bitrig`: say when Bitrig must be opened and where the prompt should be pasted.
4. `Verify`: say which local Bitrig files and index entries are being checked.
5. `Remote`: say exactly what the user must confirm on iPhone.

If any step fails, stop at the first concrete blocker, print the failed check, and give one next action. Do not continue through later steps after a failed prerequisite.

## Prompt Requirements

The prompt sent to Bitrig must be generic for any Codex iOS project:

- Include the derived Agent name, source project name, and source checkout path.
- Include the absolute Codex checkout path.
- Ask for a native Bitrig Agent project, not a Classic import.
- Ask for an iPhone-only, buildable SwiftUI shell for Bitrig Remote.
- Require a real SwiftUI app entry point, `ContentView`, iOS application target, and unique bundle identifier.
- Ask Bitrig to include a local `BitrigAgent.json` metadata file with at least:
  - `kind: "agent-project"`
  - `name`
  - `sourceProjectName`
  - `sourceProjectPath`
  - `platforms: ["iPhone"]`
  - `bundleIdentifier`
- Preserve project identity without trying to copy or compile the entire original repo unless the user explicitly requests that.

## Public Plugin Safety Rules

- Do not include personal names, fixed home-directory paths, machine names, or private project paths in generated docs, examples, manifests, or scripts.
- Do not use a Classic import as a fallback for an Agent project.
- Do not mutate Bitrig metadata directly as the primary creation path.
- Do not report success from local checks as Bitrig Remote success. The final iPhone-side confirmation belongs to the user.
- Prefer `--dry-run` first when identity, permissions, or overwrite behavior is uncertain.

## Native UI Automation Notes

Use macOS Accessibility automation when direct UI work is needed:

```bash
osascript -e 'tell application "Bitrig" to activate'
osascript -e 'tell application "System Events" to tell process "Bitrig" to click menu item "New Project" of menu "File" of menu bar 1'
pbcopy < /tmp/bitrig-agent-prompt.txt
osascript -e 'tell application "System Events" to tell process "Bitrig" to keystroke "v" using command down'
```

Coordinates may vary. Prefer named menu items and screen captures over blind clicks. If using coordinates, capture the screen before submitting.

## Troubleshooting

- If the project appears in Classic only, it is not ready for Bitrig Remote Agent. Create it again through the Agent New Project composer.
- If manual records disappear after relaunch, stop editing plist/JSON and use the native UI path.
- If Bitrig creates a project but the index has not updated yet, close the project window back to the Agent list and wait a few seconds.
- If the build fails, inspect Bitrig's shown error first. For shell projects, fix the generated Bitrig project files under `~/Library/Bitrig/Projects/<id>`, then let Bitrig rebuild.
- Keep old Classic rows unless the user explicitly asks to delete them.

## Resources

- `scripts/bitrig_agent_bridge.py`: public orchestration entrypoint for preflight, prepare, run, and verify.
- `scripts/prepare_bitrig_agent_prompt.py`: inspect a local iOS project and write a Bitrig Agent creation prompt.
- `scripts/verify_bitrig_agent_project.py`: verify the newest native Agent project by name across Bitrig's index, catalog, project folder, and metadata.
- `references/native-agent-workflow.md`: detailed notes about why native Agent creation is required and how to recover from common false positives.
