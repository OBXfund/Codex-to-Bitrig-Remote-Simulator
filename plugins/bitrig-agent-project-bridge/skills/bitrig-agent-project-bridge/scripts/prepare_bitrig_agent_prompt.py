#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
from pathlib import Path


GENERIC_NAMES = {"new project", "app", "agent", "untitled", "ios app", "project"}


def slug_words(value: str) -> list[str]:
    return [part for part in re.split(r"[^A-Za-z0-9]+", value) if part]


def pascal_case(value: str) -> str:
    words = slug_words(value)
    if not words:
        return "CodexProject"
    return "".join(word[:1].upper() + word[1:] for word in words)


def is_generic_name(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return normalized in GENERIC_NAMES


def read_project_name(path: Path) -> str:
    for xcodeproj in sorted(path.glob("*.xcodeproj")):
        return xcodeproj.stem
    for xcworkspace in sorted(path.glob("*.xcworkspace")):
        return xcworkspace.stem
    if (path / "Package.swift").exists():
        return path.name
    swift_files = sorted(path.glob("*.swift"))
    if swift_files:
        return path.name
    return path.name


def derive_agent_name(source_name: str, override: str | None) -> str:
    if override:
        if is_generic_name(override):
            raise SystemExit(
                f"Refusing generic Agent name {override!r}. Provide a specific --agent-name."
            )
        return pascal_case(override)
    if is_generic_name(source_name):
        raise SystemExit(
            f"Refusing generic source project name {source_name!r}. Provide --agent-name with a specific visible Agent name."
        )
    base = pascal_case(source_name)
    return base if base.endswith("Agent") else f"{base}Agent"


def detect_ios_capability(path: Path) -> dict:
    markers = {
        "xcodeproj": [str(p) for p in sorted(path.glob("*.xcodeproj"))],
        "xcworkspace": [str(p) for p in sorted(path.glob("*.xcworkspace"))],
        "packageSwift": (path / "Package.swift").exists(),
        "projectYml": (path / "project.yml").exists(),
        "swiftFiles": [str(p) for p in sorted(path.rglob("*.swift"))[:20]],
    }
    markers["iosCapable"] = bool(
        markers["xcodeproj"]
        or markers["xcworkspace"]
        or markers["packageSwift"]
        or markers["projectYml"]
        or markers["swiftFiles"]
    )
    return markers


def load_bundle_names(path: Path) -> list[str]:
    names = []
    for info in path.rglob("Info.plist"):
        try:
            with info.open("rb") as fh:
                plist = plistlib.load(fh)
            display = plist.get("CFBundleDisplayName") or plist.get("CFBundleName")
            if display and display not in names:
                names.append(str(display))
        except Exception:
            continue
    return names[:5]


def build_prompt(
    project: Path,
    source_name: str,
    agent_name: str,
    markers: dict,
    bundle_names: list[str],
) -> str:
    marker_summary = []
    if markers["xcodeproj"]:
        marker_summary.append(f"Xcode project: {Path(markers['xcodeproj'][0]).name}")
    if markers["xcworkspace"]:
        marker_summary.append(f"Workspace: {Path(markers['xcworkspace'][0]).name}")
    if markers["packageSwift"]:
        marker_summary.append("Package.swift present")
    if markers["projectYml"]:
        marker_summary.append("project.yml present")
    if bundle_names:
        marker_summary.append("Bundle display names: " + ", ".join(bundle_names))
    if not marker_summary:
        marker_summary.append("Swift/iOS source files detected")

    return (
        f"Create an iPhone app named {agent_name} as a native Bitrig Agent project so Bitrig Remote "
        "can open it under Agent on iPhone. Build a lightweight, buildable SwiftUI shell that "
        f"represents the local Codex iOS project named {source_name} at {project}. Do not import it as Classic. "
        "Do not try to copy or compile the entire checkout unless needed for a small preview shell. "
        "Use the source project identity and include the checkout path visibly in the app so the "
        "user knows which Codex project this Agent project represents. "
        f"Detected project context: {'; '.join(marker_summary)}. "
        "Create a real iOS application target with a SwiftUI App entry point, ContentView, and a "
        "unique bundle identifier that does not reuse the source app's bundle identifier. "
        "Create a local BitrigAgent.json file in the Bitrig project root with JSON metadata: "
        f'kind \"agent-project\", name \"{agent_name}\", sourceProjectName \"{source_name}\", '
        f'sourceProjectPath \"{project}\", platforms [\"iPhone\"], bundleIdentifier, '
        "and a short projectSummary. Keep the Bitrig app iPhone-only, SwiftUI-based, and buildable in Bitrig."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a native Bitrig Agent project prompt for a Codex iOS project.")
    parser.add_argument("--project", required=True, help="Absolute or relative path to the Codex iOS project")
    parser.add_argument("--name", help="Override the source project name used for identity")
    parser.add_argument("--agent-name", help="Override the visible Bitrig Agent project name")
    parser.add_argument("--output", help="Write prompt to this file")
    parser.add_argument("--json", action="store_true", help="Print JSON metadata instead of plain prompt")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not project.exists():
        raise SystemExit(f"Project path does not exist: {project}")
    if not project.is_dir():
        raise SystemExit(f"Project path is not a directory: {project}")

    markers = detect_ios_capability(project)
    if not markers["iosCapable"]:
        raise SystemExit(f"No iOS-capable project markers found in {project}")

    source_name = args.name or read_project_name(project)
    agent_name = derive_agent_name(source_name, args.agent_name)
    bundle_names = load_bundle_names(project)
    prompt = build_prompt(project, source_name, agent_name, markers, bundle_names)

    result = {
        "schemaVersion": "1.0",
        "status": "prepared",
        "projectPath": str(project),
        "sourceProjectName": source_name,
        "agentName": agent_name,
        "markers": markers,
        "bundleNames": bundle_names,
        "prompt": prompt,
    }

    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(prompt + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
